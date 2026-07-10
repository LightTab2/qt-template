#!/usr/bin/env python3
"""WARNING: vibe coded. Works, but read with suspicion before extending.

Restore the declaration line Doxygen drops from member-detail inline-source fragments.

With INLINE_SOURCES=YES + SOURCE_BROWSER=YES (doxygen/Doxyfile), a member's detail page
shows "Definition at line N of file F" followed by the member's inline source - but Doxygen
starts that fragment at the line AFTER the declaration, so a member documented at line N is
rendered starting at line N+1 (its body/`{`), dropping the signature line(s). This post-
processor prepends the missing rendered source lines N..F1-1 - pulled from the already-
generated F_source.html page, NOT re-parsed from C++ - so the fragment begins at line N.

Transform, applied to every member page (docs/html/*.html, skipping *_source.html):
  For each `<p class="definition">Definition at line <a ..#lNNNNN>N</a> of file <a ..>F</a>.</p>`
  IMMEDIATELY followed by `<div class="fragment"> ... </div><!-- fragment -->` (contract C5),
  let F1 be the fragment's first `span.lineno` value. When the definition names ONE consistent
  source file F (both hrefs agree) AND F1 > N, prepend the rendered source lines N..F1-1 from
  F_source.html, each with its leading per-line `<a id/name="lNNNNN"></a>` anchor stripped (so
  no duplicate-id / foreign anchor lands in the fragment; span.lineno + code spans/links are
  kept), so the fragment's new first line is N. Generalizes to multi-line signatures
  (F1 = N+2 prepends both line N and line N+1).

Guard / no-ops (no false positives):
  - F1 <= N: unchanged. Covers one-line members already rendered at their declaration
    (F1 == N) and class-level definitions that point at a header while the fragment is from a
    .cpp (the fragment's line numbering is offset, so F1 < N) - Doxygen never mislabels these
    upward, so F1 <= N is the reliable "leave it alone" signal.
  - Because the fragment carries no source-file marker of its own, the definition paragraph is
    the only file signal: the immediately-following fragment IS that member's inline source
    (INLINE_SOURCES), so "fragment source file" == the definition's F. We verify the definition
    paragraph names ONE file (its `#lNNNNN` href and its "of file" href agree) and that every
    prepended line N..F1-1 exists in F_source.html; a definition whose file truly differs from
    its fragment surfaces as F1 <= N and is left untouched.

Offline + idempotent + fail-soft (contract C6): reads only already-generated docs/html
(no network, no C++ re-parse); after a splice the fragment's first line IS N, so on a second
pass F1 == N, the F1 > N guard is false, and the output is byte-identical; per-fragment work
is wrapped try/except -> warn to stderr -> continue, so a missing F_source.html, an
inconsistent/unparseable definition paragraph, or an out-of-range source line is warned and
SKIPPED while the other members on the page still process and the whole `make docs` (which
runs under `set -euo pipefail`) never aborts. `main(html_dir)` returns 0 on partial success;
hard non-zero only when html_dir is absent (a truly unusable invocation). Runs from
scripts/run_doxygen.sh, gated by PVN_RESTORE_DEFLINE (PVN_GRAPH_FILTER semantics:
`${PVN_RESTORE_DEFLINE:-1} != "0"` means on).

Version coupling (contract C7): the definition-paragraph, fragment, and source-page line
shapes are Doxygen 1.17.0 specific - the omitted-declaration-line behavior and this exact
markup are what the regexes below are keyed to.

Usage: restore_definition_line.py <html-dir>   (default docs/html)
Env:   PVN_RESTORE_DEFLINE  =0 disables the step (handled by the driver, not here)
"""

import os
import re
import sys

# --- Doxygen 1.17.0 output-DOM patterns (contract C5, frozen) ------------------------

# The definition paragraph: two `href="F_source.html..."` links, the first carrying the
# `#lNNNNN` line anchor with visible line number N, the second the bare "of file F" link.
_DEFINITION_RE = re.compile(
    r'<p class="definition">Definition at line '
    r'<a class="el" href="([^"#]+)#l\d+">(\d+)</a> of file '
    r'<a class="el" href="([^"#]+)">[^<]*</a>\.</p>')

# A whole member fragment: the definition paragraph, the whitespace + `<div class="fragment">`
# open, the inner lines, and the `</div><!-- fragment -->` close. Non-greedy `inner` stops at
# the first fragment terminator, so each member's fragment is matched independently and the
# untouched parts (defpara, gap, suffix) round-trip byte-for-byte.
_DEF_FRAGMENT_RE = re.compile(
    r'(?P<defpara><p class="definition">Definition at line '
    r'<a class="el" href="[^"#]+#l\d+">\d+</a> of file '
    r'<a class="el" href="[^"#]+">[^<]*</a>\.</p>)'
    r'(?P<gap>\s*<div class="fragment">)'
    r'(?P<inner>.*?)'
    r'(?P<suffix></div><!-- fragment -->)',
    re.DOTALL)

# A source-page line: `<div class="line"><a id="lNNNNN" name="lNNNNN"></a>...code...</div>`.
# `[^\n]*?` keeps each match on its own physical line (Doxygen emits one per source line).
_SOURCE_LINE_RE = re.compile(
    r'<div class="line"><a id="l(\d+)" name="l\d+"></a>[^\n]*?</div>')

# The leading per-line anchor to strip from a prepended source line (AC26.1).
_LINE_ANCHOR_RE = re.compile(r'(<div class="line">)<a id="l\d+" name="l\d+"></a>')

# The fragment's first line number: the digits inside the first `<span class="lineno">`,
# which may wrap the number in an `<a class="line" ...>` self-link on the source page.
_FRAGMENT_LINENO_RE = re.compile(r'<span class="lineno">\s*(?:<a\b[^>]*>)?\s*(\d+)')


def _warn(message):
    """Fail-soft warning to stderr (contract C6); processing continues past it."""
    sys.stderr.write("[restore-defline] WARNING: %s\n" % message)


# --- pure functions (unit-tested) ---------------------------------------------------

def parse_definition_paragraph(text):
    """Return (source_file, N) parsed from a `<p class="definition">` paragraph, or None
    when it is absent, unparseable, or names two different files in its two hrefs (an
    inconsistent definition - the frozen "definition source file equals the fragment source
    file" guard: both hrefs must name the one file the fragment was inlined from)."""
    m = _DEFINITION_RE.search(text)
    if not m:
        return None
    source_file, defline, of_file = m.group(1), int(m.group(2)), m.group(3)
    if source_file != of_file:
        return None
    return source_file, defline


def index_source_lines(source_html):
    """Index a rendered `*_source.html` page's `<div class="line">` blocks by line number:
    {N: full_line_block}. Each block still carries its leading `<a id/name>` anchor;
    strip_line_anchor removes it at prepend time."""
    return {int(m.group(1)): m.group(0) for m in _SOURCE_LINE_RE.finditer(source_html)}


def strip_line_anchor(line_block):
    """Drop the leading per-line `<a id="lNNNNN" name="lNNNNN"></a>` from a source line block
    so no duplicate-id / foreign anchor enters the member fragment (AC26.1). The span.lineno
    and every code span / link after it are preserved untouched."""
    return _LINE_ANCHOR_RE.sub(r'\1', line_block, count=1)


def first_fragment_lineno(fragment_inner):
    """Return the fragment's first `span.lineno` value (F1), or None when the fragment has
    no line. Handles both the plain member-fragment lineno and a source-line lineno whose
    number is wrapped in an `<a class="line" ...>` self-link."""
    m = _FRAGMENT_LINENO_RE.search(fragment_inner)
    return int(m.group(1)) if m else None


def build_restored_inner(prepend_blocks, original_inner):
    """Prepend the (already anchor-stripped) source line blocks before the fragment's own
    lines, matching Doxygen's one-`div.line`-per-newline layout so the spliced fragment is
    byte-shaped like a native one."""
    return "".join(block + "\n" for block in prepend_blocks) + original_inner


# --- whole-document transform (fail-soft per fragment) ------------------------------

def restore_definition_line(text, source_reader):
    """Return `text` with every member fragment whose declaration line was dropped restored.
    `source_reader(basename)` returns the {line_no: block} index for that `*_source.html`
    page, or None when it is missing. Each fragment is spliced independently and fail-soft:
    any problem warns and leaves that fragment unchanged (contract C6)."""

    def _restore(match):
        try:
            parsed = parse_definition_paragraph(match.group("defpara"))
            if parsed is None:
                _warn("skipped an unparseable/inconsistent definition paragraph")
                return match.group(0)
            source_file, defline = parsed
            inner = match.group("inner")
            frag_first = first_fragment_lineno(inner)
            if frag_first is None or frag_first <= defline:
                return match.group(0)  # F1 <= N: already at (or below) the declaration - no-op
            index = source_reader(source_file)
            if index is None:
                _warn("missing source page %s; kept fragment as-is" % source_file)
                return match.group(0)
            prepend_blocks = []
            for line_no in range(defline, frag_first):
                block = index.get(line_no)
                if block is None:
                    _warn("line %d out of range in %s; kept fragment as-is"
                          % (line_no, source_file))
                    return match.group(0)
                prepend_blocks.append(strip_line_anchor(block))
            restored_inner = build_restored_inner(prepend_blocks, inner)
            return match.group("defpara") + match.group("gap") + restored_inner + match.group("suffix")
        except Exception as exc:  # noqa: BLE001 - one bad fragment must not abort the page
            _warn("splice failed: %s" % exc)
            return match.group(0)

    return _DEF_FRAGMENT_RE.sub(_restore, text)


# --- CLI ----------------------------------------------------------------------------

def _make_source_reader(html_dir):
    """A caching `basename -> {line_no: block} index or None` reader over html_dir's
    `*_source.html` pages (offline, contract C6/AC26.3). A missing page caches None."""
    cache = {}

    def reader(basename):
        if basename not in cache:
            path = os.path.join(html_dir, basename)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    cache[basename] = index_source_lines(f.read())
            else:
                cache[basename] = None
        return cache[basename]

    return reader


def restore_file(path, source_reader):
    """Rewrite one member page in place, restoring dropped declaration lines. Return True
    when the file content changed, False when it is already correct (byte-identical)."""
    with open(path, encoding="utf-8") as f:
        original = f.read()
    updated = restore_definition_line(original, source_reader)
    if updated != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)
        return True
    return False


def main(html_dir):
    """Restore dropped declaration lines across every member page in html_dir (skipping the
    `*_source.html` browser pages we read from). Fail-soft: a bad page is warned and skipped;
    returns 0 on partial success, non-zero only when html_dir is missing."""
    if not os.path.isdir(html_dir):
        sys.stderr.write("[restore-defline] not a directory: %s\n" % html_dir)
        return 1
    source_reader = _make_source_reader(html_dir)
    changed = 0
    for name in sorted(os.listdir(html_dir)):
        if not name.endswith(".html") or name.endswith("_source.html"):
            continue
        path = os.path.join(html_dir, name)
        try:
            if restore_file(path, source_reader):
                changed += 1
        except Exception as exc:  # noqa: BLE001 - one bad page must not abort the build
            sys.stderr.write("[restore-defline] WARNING: skipped %s: %s\n" % (name, exc))
            continue
    print("[restore-defline] %d pages rewritten in %s" % (changed, html_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/html"))
