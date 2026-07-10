#!/usr/bin/env python3
"""WARNING: vibe coded. Works, but read with suspicion before extending.

Post-process Doxygen's client-side search index (docs/html/search/*.js) so search
shows only project-authored symbols, each project class carrying an excerpt line.

Two transforms, applied to every `var searchData=[ ... ];` data file:
  1. Drop external results. Each entry's result list is pruned of absolute-URL
     (http://, https:// - i.e. Qt tag-file) results; an entry left with zero results
     is removed entirely. So an entry ALL of whose results are external disappears, a
     MIXED entry (a project symbol that shares a name with a Qt symbol, e.g. `raise`,
     `clone`, `operator<<`) keeps only its project result, and no `doc.qt.io` URL
     survives anywhere (R1 / AC1.1). A file emptied of every entry is rewritten as
     `var searchData=[];`, never deleted (AC1.3 - a deleted letter file would 404).
  2. Inject class excerpts. For each surviving SINGLE-RESULT class entry (a file whose
     basename is `classes_*.js`, entry with `len(entry[1]) == 2`), the entry's scope
     field `entry[1][1][2]` is set to the class's trimmed, HTML-escaped brief, read
     from the already-generated class page. Doxygen's search.js renders that string
     into span.SRScope (the card excerpt line, contract C3 / R2). Multi-result entries
     are left untouched: for them `entry[1][1][2]` is child-0's overload-disambiguation
     scope and writing it would clobber it.

The brief is the first `<div class="textblock">` `<p>` that is NOT `<p class="definition">`.
A briefless class's only textblock `<p>` IS `<p class="definition">Definition at line N of
file F.</p>`; that is the normal empty-scope case - the definition line is NEVER injected
and the scope is left empty (AC2.2). Non-class categories keep their scopes (AC2.3).

Offline + idempotent + fail-soft (contract C6): reads only already-generated docs/html
(no network, no C++ re-parse); a second pass over processed output is byte-identical (the
serializer is a fixed point of the parser and briefs recompute to the same string); and
per-file / per-entry work is wrapped try/except -> warn to stderr -> continue, so one bad
page never aborts the file or the whole `make docs` (which runs under `set -euo pipefail`).
`main(search_dir)` returns 0 on partial success; hard non-zero only when search_dir is
absent. Runs from scripts/run_doxygen.sh, gated by PVN_SEARCH_FILTER (PVN_GRAPH_FILTER
semantics: `${PVN_SEARCH_FILTER:-1} != "0"` means on).

Version coupling (contract C7): the entry shapes and the class-page textblock/definition
DOM are Doxygen 1.17.0 specific. The name/scope escaping matches Doxygen's own JS-string
escaping (search.js renders each via `decodeHtml(...)` -> innerHTML), and Doxygen never
emits a raw single quote in these strings (it entity-escapes them), so the single-quote
serialization below stays valid JS.

Usage: filter_search_index.py <search-dir>   (default docs/html/search)
Env:   PVN_SEARCH_FILTER  =0 disables the step (handled by the driver, not here)
"""

import ast
import html
import os
import re
import sys

# --- external classifier (frozen, contract C3) -------------------------------------

def is_external(url):
    """True when url is an absolute (http/https) link - a Qt tag-file target to drop."""
    return url.startswith("http://") or url.startswith("https://")


# --- search-data parse / serialize (Doxygen 1.17.0 `var searchData=[...]`) ----------
# Each data file is `var searchData=\n[\n  <entry>,\n  ...\n];\n`. An entry is a
# Python-list-literal-shaped node (single-quoted strings, ints) so ast.literal_eval reads
# it exactly; the serializer below reproduces Doxygen's byte format so a file with nothing
# to change round-trips identically (unchanged files stay byte-identical, re-runs are no-ops).

def parse_search_data(text):
    """Parse a search data file body to a list of entries, or None when `text` is not a
    `var searchData=[...]` file (search.js engine, searchdata.js index sections)."""
    stripped = text.strip()
    if not stripped.startswith("var searchData="):
        return None
    body = stripped[len("var searchData="):].rstrip()
    if not body.endswith(";"):
        return None
    return ast.literal_eval(body[:-1])


def _serialize_node(node):
    """Serialize one JS node (str / int / list) back to Doxygen's compact single-quote form."""
    if isinstance(node, str):
        # Doxygen entity-escapes special chars, and injected briefs are html.escape()d, so no
        # raw single quote reaches here - single-quote wrapping stays valid JS (matches Doxygen).
        # html.escape does NOT touch a backslash, though, and injected briefs are whitespace-
        # collapsed (extract_brief) so control chars never reach here - the one residual hole is
        # a literal '\' (a brief ending in '\' would escape the closing quote and leave that
        # letter file's JS unterminated). Double it, preserving the single-quote byte format so
        # backslash-free content (all current scopes/briefs) still round-trips identically.
        return "'" + node.replace("\\", "\\\\") + "'"
    if isinstance(node, bool):  # bool is an int subclass; keep it out of the int branch
        return "1" if node else "0"
    if isinstance(node, int):
        return str(node)
    if isinstance(node, list):
        return "[" + ",".join(_serialize_node(n) for n in node) + "]"
    raise TypeError("unserializable search node: %r" % (node,))


def serialize_search_data(entries):
    """Render entries back to a `var searchData=...;` file. Empty -> `var searchData=[];`
    (AC1.3). Byte-format matches Doxygen 1.17.0 so unchanged files are identical."""
    if not entries:
        return "var searchData=[];\n"
    body = ",\n".join("  " + _serialize_node(entry) for entry in entries)
    return "var searchData=\n[\n" + body + "\n];\n"


# --- transform 1: drop external results ---------------------------------------------

def filter_external(entries):
    """Return a new entry list with every external result pruned and every entry that is
    left with zero results removed. An all-external entry disappears; a mixed entry keeps
    only its project results (so no doc.qt.io URL survives, AC1.1)."""
    kept = []
    for entry in entries:
        entry_id, payload = entry[0], entry[1]
        name, results = payload[0], payload[1:]
        local = [r for r in results if not is_external(r[0])]
        if not local:
            continue  # every result was external -> drop the whole entry
        kept.append([entry_id, [name] + local])
    return kept


# --- transform 2: class-brief extraction + injection --------------------------------

_TEXTBLOCK_RE = re.compile(r'<div class="textblock"\s*>')
_P_OPEN_RE = re.compile(r'<p(\s[^>]*)?>')
_TAG_RE = re.compile(r'<[^>]+>')


class MissingTextblock(Exception):
    """The class page has no `<div class="textblock">` at all - warn and skip (C6)."""


def _matching_div_close(text, pos):
    """Index of the `</div>` that closes the div whose content starts at `pos`
    (depth-counted so nested divs in the textblock do not end the region early)."""
    depth = 1
    i = pos
    while i < len(text):
        o = text.find("<div", i)
        c = text.find("</div>", i)
        if c == -1:
            return -1
        if o != -1 and o < c:
            depth += 1
            i = o + 4
        else:
            depth -= 1
            i = c + 6
            if depth == 0:
                return c
    return -1


def extract_brief(page_html):
    """Return the class's trimmed, HTML-escaped brief: the first textblock `<p>` that is
    NOT `<p class="definition">`, with inner markup stripped and text re-escaped Doxygen-
    style. Return '' when the class is briefless (textblock present, only the definition
    paragraph). Raise MissingTextblock when there is no textblock div at all."""
    m = _TEXTBLOCK_RE.search(page_html)
    if not m:
        raise MissingTextblock()
    start = m.end()
    end = _matching_div_close(page_html, start)
    region = page_html[start:end] if end >= 0 else page_html[start:]
    for pm in _P_OPEN_RE.finditer(region):
        if 'class="definition"' in pm.group(0):
            continue  # the appended "Definition at line N of file F." - never the brief
        close = region.find("</p>", pm.end())
        inner = region[pm.end():close] if close >= 0 else region[pm.end():]
        text = _TAG_RE.sub("", inner)        # drop nested markup (e.g. a Qt <a> link)
        text = html.unescape(text)           # entities -> characters
        text = " ".join(text.split())        # trim + collapse whitespace
        return html.escape(text, quote=True)  # re-escape consistently with the name field
    return ""  # only a definition paragraph (or no <p>): briefless -> empty scope


def class_brief(search_dir, url):
    """Load the class page the entry points to and return its escaped brief. The page is
    resolved RELATIVE TO the search dir (project URLs look like `../classMainWindow.html`).
    Raise (missing file / MissingTextblock) so the caller warns and skips (C6).

    A member-anchored URL (`../file_8h.html#structFoo`) points a type INTO a compound page
    whose first textblock <p> is the FILE brief, not the type's - extracting it would inject
    a wrong excerpt, and the un-stripped `#...` also breaks os.path.isfile and warns every
    build. Strip the fragment and, when there was one, skip quietly (return '') rather than
    resolve the compound page or warn."""
    path_part, _, fragment = url.partition("#")
    if fragment:
        return ""  # anchored type: no reliable per-type brief in the compound page; skip quietly
    page_path = os.path.normpath(os.path.join(search_dir, path_part))
    if not os.path.isfile(page_path):
        raise FileNotFoundError(page_path)
    with open(page_path, encoding="utf-8") as f:
        return extract_brief(f.read())


def inject_brief(entry, search_dir):
    """Set a SINGLE-RESULT class entry's scope field `entry[1][1][2]` to its class brief.
    Multi-result entries (`len(entry[1]) != 2`) are left untouched (that slot is child-0's
    overload scope, C3). Raises on an unresolvable / textblock-less page (caller warns)."""
    payload = entry[1]
    if len(payload) != 2:
        return  # multi-result: never write child-0's scope
    result = payload[1]
    if is_external(result[0]):
        return  # defensive: never inject into an external result (filter already dropped these)
    result[2] = class_brief(search_dir, result[0])


# --- per-file transform + CLI -------------------------------------------------------

def transform_file(path, search_dir):
    """Rewrite one search data file in place: drop external results, then (classes_*.js
    only) inject single-result class briefs. Per-entry brief lookup is fail-soft. Return
    True when the file content changed, False when unchanged or not a data file."""
    with open(path, encoding="utf-8") as f:
        original = f.read()
    entries = parse_search_data(original)
    if entries is None:
        return False  # search.js / searchdata.js and friends: not our data files
    entries = filter_external(entries)
    if os.path.basename(path).startswith("classes_"):
        for entry in entries:
            try:
                inject_brief(entry, search_dir)
            except Exception as exc:  # noqa: BLE001 - one bad page must not abort the file
                sys.stderr.write(
                    "[search-filter] WARNING: no excerpt for %r in %s: %s\n"
                    % (entry[1][0], os.path.basename(path), exc))
                continue
    new_text = serialize_search_data(entries)
    if new_text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
        return True
    return False


def main(search_dir):
    """Post-process every `*.js` search data file in search_dir. Fail-soft: a bad file is
    warned and skipped; returns 0 on partial success, non-zero only when search_dir is
    missing (a truly unusable invocation)."""
    if not os.path.isdir(search_dir):
        sys.stderr.write("[search-filter] not a directory: %s\n" % search_dir)
        return 1
    changed = 0
    for name in sorted(os.listdir(search_dir)):
        if not name.endswith(".js") or name == "search.js":
            continue
        path = os.path.join(search_dir, name)
        try:
            if transform_file(path, search_dir):
                changed += 1
        except Exception as exc:  # noqa: BLE001 - one bad file must not abort the build
            sys.stderr.write("[search-filter] WARNING: skipped %s: %s\n" % (name, exc))
            continue
    print("[search-filter] %d search data files rewritten in %s" % (changed, search_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/html/search"))
