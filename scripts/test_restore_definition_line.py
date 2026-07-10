#!/usr/bin/env python3
"""Standalone python3 asserts for restore_definition_line.py (no pytest, matches the repo).

Run: python3 scripts/test_restore_definition_line.py
Every R25-R26 acceptance criterion the post-processor owns is exercised here; the
definition-paragraph / fragment / source-line fixtures are Doxygen 1.17.0 shaped
(contract C7), lifted from a real classAppException.html + Exceptions_8cpp_source.html build.
"""

import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import restore_definition_line as rdl  # noqa: E402


# --- fixtures (Doxygen 1.17.0 markup, Exceptions.cpp: 6 = ctor, 8 = raise()) ---------

SRC = "Exceptions_8cpp_source.html"

# One rendered source-page line per line number, each with its leading id/name anchor.
SRC_LINE = {
    6: ('<div class="line"><a id="l00006" name="l00006"></a>'
        '<span class="lineno"><a class="line" href="classAppException.html#ctor">    6</a></span>'
        '<a class="code hl_function" href="classAppException.html#ctor">AppException::AppException</a>'
        '(<span class="keyword">const</span> <span class="keywordtype">char</span>* msg) {}</div>'),
    7: ('<div class="line"><a id="l00007" name="l00007"></a>'
        '<span class="lineno">    7</span> </div>'),
    8: ('<div class="line"><a id="l00008" name="l00008"></a>'
        '<span class="lineno"><a class="line" href="classAppException.html#raise">    8</a></span>'
        '<span class="keywordtype">void</span> '
        '<a class="code hl_function" href="classAppException.html#raise">AppException::raise</a>'
        '()<span class="keyword"> const</span></div>'),
    9: ('<div class="line"><a id="l00009" name="l00009"></a>'
        '<span class="lineno">    9</span><span class="keyword"></span>{</div>'),
    10: ('<div class="line"><a id="l00010" name="l00010"></a>'
         '<span class="lineno">   10</span>    <span class="keywordflow">throw</span> '
         '*<span class="keyword">this</span>;</div>'),
    11: ('<div class="line"><a id="l00011" name="l00011"></a>'
         '<span class="lineno">   11</span>}</div>'),
}

SOURCE_PAGE = "\n".join(SRC_LINE[n] for n in sorted(SRC_LINE)) + "\n"


def _reader(index):
    """Return a source_reader closure over a fixed {basename: index} map."""
    def reader(basename):
        return index.get(basename)
    return reader


def _def_para(line, srcfile=SRC, disp="Exceptions.cpp", of_file=None):
    of_file = of_file or srcfile
    return ('<p class="definition">Definition at line '
            '<a class="el" href="%s#l%05d">%d</a> of file '
            '<a class="el" href="%s">%s</a>.</p>' % (srcfile, line, line, of_file, disp))


def _fragment(*line_numbers):
    """A member fragment (NO id/name anchors, as Doxygen renders inline source) whose
    div.line spans wrap the given source line numbers - the body Doxygen shows, with the
    declaration line already dropped."""
    lines = []
    for i, n in enumerate(line_numbers):
        # strip the id anchor + reduce the lineno to the plain member-fragment shape
        body = rdl.strip_line_anchor(SRC_LINE[n])
        body = body.replace(
            '<span class="lineno"><a class="line" href="classAppException.html#raise">    8</a></span>',
            '<span class="lineno">    8</span>')
        lines.append(body)
    inner = "\n".join(lines) + "\n"
    return '<div class="fragment">' + inner + '</div><!-- fragment -->'


def _page(def_line, *frag_line_numbers, **kw):
    return _def_para(def_line, **kw) + "\n" + _fragment(*frag_line_numbers)


# --- parse N / F from a definition paragraph (AC25.1 precondition) -------------------

def test_parse_definition_paragraph():
    assert rdl.parse_definition_paragraph(_def_para(8)) == (SRC, 8)
    assert rdl.parse_definition_paragraph(_def_para(29, srcfile="Exceptions_8h_source.html",
                                                    disp="Exceptions.h")) == (
        "Exceptions_8h_source.html", 29)


def test_parse_rejects_inconsistent_files():
    # first href names the header, "of file" names the cpp -> not a single-file definition
    para = _def_para(29, srcfile="Exceptions_8h_source.html", disp="Exceptions.cpp",
                     of_file=SRC)
    assert rdl.parse_definition_paragraph(para) is None


def test_parse_rejects_non_definition():
    assert rdl.parse_definition_paragraph("<p>Reimplemented from QException.</p>") is None


# --- index a source page's div.line by number (AC25.1 precondition) ------------------

def test_index_source_lines():
    index = rdl.index_source_lines(SOURCE_PAGE)
    assert set(index) == {6, 7, 8, 9, 10, 11}
    assert index[8] == SRC_LINE[8]


# --- strip the leading per-line anchor (AC26.1) -------------------------------------

def test_strip_line_anchor():
    stripped = rdl.strip_line_anchor(SRC_LINE[8])
    assert 'id="l00008"' not in stripped
    assert 'name="l00008"' not in stripped
    assert stripped.startswith('<div class="line"><span class="lineno">')
    # span.lineno kept, and the code link to AppException::raise preserved (AC26.1)
    assert '<span class="lineno">' in stripped
    assert 'AppException::raise' in stripped
    assert 'href="classAppException.html#raise"' in stripped


def test_strip_line_anchor_leaves_code_anchors():
    # only the LEADING id/name anchor goes; a code <a> further in the line stays
    stripped = rdl.strip_line_anchor(SRC_LINE[6])
    assert 'id="l00006"' not in stripped
    assert 'href="classAppException.html#ctor"' in stripped  # code link untouched


# --- splice: F1 = N+1 gains line N, now starts at N (AC25.1 / AC25.2) ----------------

def test_splice_single_line_prepends_declaration():
    page = _page(8, 9, 10, 11)  # "Definition at line 8" but fragment starts at 9
    out = rdl.restore_definition_line(page, _reader({SRC: rdl.index_source_lines(SOURCE_PAGE)}))
    inner = out.split('<div class="fragment">', 1)[1]
    assert rdl.first_fragment_lineno(inner) == 8            # now starts at 8 (was 9)
    first_line = inner.split("\n", 1)[0]
    assert 'AppException::raise' in first_line              # AC25.2: decl on the first line
    assert inner.count('<div class="line">') == 4           # 8,9,10,11
    assert 'id="l00008"' not in out                         # AC26.1: no foreign anchor


# --- multi-line signature: F1 = N+2 prepends both N and N+1 --------------------------

def test_splice_multiline_prepends_both():
    page = _page(8, 10, 11)  # 2-line "signature" 8-9 dropped, fragment starts at 10
    out = rdl.restore_definition_line(page, _reader({SRC: rdl.index_source_lines(SOURCE_PAGE)}))
    inner = out.split('<div class="fragment">', 1)[1]
    assert rdl.first_fragment_lineno(inner) == 8
    blocks = [b for b in inner.split("\n") if b.startswith('<div class="line">')]
    assert rdl.first_fragment_lineno(blocks[0]) == 8
    assert rdl.first_fragment_lineno(blocks[1]) == 9
    assert rdl.first_fragment_lineno(blocks[2]) == 10


# --- guard: F1 <= N leaves the fragment unchanged (AC25.3) ---------------------------

def test_guard_offset_mismatch_unchanged():
    # class-level "line 29" (header) but the fragment is a .cpp body starting at 7: F1 < N.
    # The source_reader RAISES if consulted, proving the guard short-circuits before any read.
    def exploding_reader(_basename):
        raise AssertionError("source must not be read when F1 <= N")
    page = _def_para(29) + "\n" + _fragment(7, 8)  # fragment first lineno 7 <= 29
    out = rdl.restore_definition_line(page, exploding_reader)
    assert out == page


def test_guard_already_at_declaration_unchanged():
    # one-line member already rendered at its declaration: F1 == N == 6 -> no-op (AC25.3)
    page = _def_para(6) + "\n" + _fragment(6)
    out = rdl.restore_definition_line(page, _reader({SRC: rdl.index_source_lines(SOURCE_PAGE)}))
    assert out == page


# --- fail-soft (C6): missing source page warned + skipped, no raise ------------------

def test_failsoft_missing_source_page():
    page = _page(8, 9, 10, 11)
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = rdl.restore_definition_line(page, _reader({}))  # SRC absent -> reader returns None
    assert out == page                       # unchanged
    assert "WARNING" in err.getvalue()
    assert "missing source page" in err.getvalue()


# --- fail-soft (C6): out-of-range source line warned + skipped -----------------------

def test_failsoft_out_of_range_line():
    page = _page(8, 9, 10, 11)
    # index is missing line 8, so the prepend range hits a hole
    partial = {n: SRC_LINE[n] for n in (9, 10, 11)}
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = rdl.restore_definition_line(page, _reader({SRC: partial}))
    assert out == page
    assert "out of range" in err.getvalue()


# --- fail-soft (C6): unparseable/inconsistent definition warned + skipped ------------

def test_failsoft_inconsistent_definition():
    para = _def_para(8, srcfile="Exceptions_8h_source.html", disp="Exceptions.cpp",
                     of_file=SRC)
    page = para + "\n" + _fragment(9, 10, 11)
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = rdl.restore_definition_line(page, _reader({SRC: rdl.index_source_lines(SOURCE_PAGE)}))
    assert out == page
    assert "unparseable/inconsistent" in err.getvalue()


# --- fail-soft (C6): a bad fragment is skipped while a good one still processes -------

def test_failsoft_isolates_one_bad_fragment():
    good = _page(8, 9, 10, 11)                       # restorable from SRC
    # a second member whose source page (mainwindow.cpp) the reader does NOT have: F1=19 > N=18
    # passes the guard, then source_reader returns None -> that fragment is warned and skipped.
    bad = (_def_para(18, srcfile="mainwindow_8cpp_source.html", disp="mainwindow.cpp")
           + '\n<div class="fragment"><div class="line"><span class="lineno">   19</span>'
             '    <span class="keywordflow">return</span>;</div>\n</div><!-- fragment -->')
    page = good + "\n<hr>\n" + bad
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = rdl.restore_definition_line(page, _reader({SRC: rdl.index_source_lines(SOURCE_PAGE)}))
    # good fragment restored (line 8 prepended), bad one left intact, transform did not raise
    good_part, bad_part = out.split("<hr>")
    assert 'AppException::raise' in good_part
    assert rdl.first_fragment_lineno(good_part.split('<div class="fragment">')[1]) == 8
    assert bad_part == "\n" + bad            # bad fragment byte-identical (skipped)
    assert "missing source page" in err.getvalue()


# --- idempotence (AC26.2): transform twice == once, byte-identical -------------------

def test_idempotent():
    page = _page(8, 9, 10, 11)
    reader = _reader({SRC: rdl.index_source_lines(SOURCE_PAGE)})
    once = rdl.restore_definition_line(page, reader)
    twice = rdl.restore_definition_line(once, reader)
    assert once != page          # first pass changed something
    assert twice == once         # second pass is a byte-identical no-op


# --- CLI: main over a temp docs dir, and hard-fail only on a missing dir -------------

def test_main_missing_dir_returns_nonzero():
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = rdl.main("/nonexistent-html-dir-xyz")
    assert rc == 1
    assert "not a directory" in err.getvalue()


def test_main_end_to_end():
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        # SRC is a *_source.html page: it is read for prepends but skipped as an input page
        with open(os.path.join(root, SRC), "w", encoding="utf-8") as f:
            f.write("<html>%s</html>" % SOURCE_PAGE)
        member = os.path.join(root, "classAppException.html")
        with open(member, "w", encoding="utf-8") as f:
            f.write("<html>%s</html>" % _page(8, 9, 10, 11))
        rc = rdl.main(root)
        assert rc == 0
        out = open(member, encoding="utf-8").read()
        inner = out.split('<div class="fragment">', 1)[1]
        assert rdl.first_fragment_lineno(inner) == 8
        assert 'AppException::raise' in inner.split("\n", 1)[0]
        # re-run is a byte-identical no-op (AC26.2 at the CLI level)
        before = open(member, encoding="utf-8").read()
        rdl.main(root)
        assert open(member, encoding="utf-8").read() == before


# --- runner -------------------------------------------------------------------------

def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print("OK: %d tests passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
