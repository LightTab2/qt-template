#!/usr/bin/env python3
"""Standalone python3 asserts for filter_search_index.py (no pytest, matches the repo).

Run: python3 scripts/test_filter_search_index.py
Every R1-R3 acceptance criterion the post-processor owns is exercised here; the DOM /
entry fixtures are Doxygen 1.17.0 shaped (contract C7). Class-page fixtures live one level
above the `search/` dir, mirroring the real `../classFoo.html` relative URLs so
class_brief() resolves them exactly as it does in a real build.
"""

import contextlib
import copy
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filter_search_index as fsi  # noqa: E402


# --- fixtures -----------------------------------------------------------------------

BRIEF_PAGE = (
    '<div class="textblock"><p>Some class. </p>\n'
    '<p>Renders a window, I guess. </p>\n'
    '<p class="definition">Definition at line <a href="x">31</a> of file '
    '<a href="y">mainwindow.h</a>.</p>\n</div>')

# brief with nested markup (a Qt <a> link) + an entity, to prove tag-strip + re-escape
MARKUP_PAGE = (
    '<div class="textblock"><p>An exception from '
    '<a class="elRef" href="https://doc.qt.io/qt-6/qt.html">Qt</a> &amp; more </p>\n'
    '<p class="definition">Definition at line 29 of file Exceptions.h.</p></div>')

# briefless: the ONLY textblock <p> is the definition paragraph
BRIEFLESS_PAGE = (
    '<div class="textblock">\n'
    '<p class="definition">Definition at line 81 of file mainwindow.h.</p>\n</div>')

# no textblock at all -> fail-soft warn+skip
NO_TEXTBLOCK_PAGE = '<html><body><h1>Nothing</h1></body></html>'


def _mk_pages(root, pages):
    """Write {basename: html} into `root` (which stands in for docs/html), return a
    `search/` subdir (which stands in for docs/html/search)."""
    for name, body in pages.items():
        with open(os.path.join(root, name), "w", encoding="utf-8") as f:
            f.write(body)
    search = os.path.join(root, "search")
    os.makedirs(search, exist_ok=True)
    return search


# --- AC1.4: external classifier -----------------------------------------------------

def test_is_external():
    assert fsi.is_external("https://doc.qt.io/qt-6/qwidget.html")
    assert fsi.is_external("http://example.com/x.html")
    assert not fsi.is_external("classMainWindow.html")
    assert not fsi.is_external("../classMainWindow.html")
    assert not fsi.is_external("../mainwindow_8h.html#structsomeStruct")


# --- filter: drop external entry, keep local (AC1.1/AC1.2 core) ---------------------

def test_filter_drops_external_entry():
    entries = [
        ["app_0", ["AppException", ["../classAppException.html", 1, ""]]],
        ["qw_1", ["QWidget", ["https://doc.qt.io/qt-6/qwidget.html", 1, ""]]],
    ]
    out = fsi.filter_external(entries)
    assert len(out) == 1
    assert out[0][1][0] == "AppException"


# --- AC1.3: an all-external file becomes `var searchData=[];` ------------------------

def test_all_external_yields_empty_array():
    entries = [["qw_0", ["QWidget", ["https://doc.qt.io/qt-6/qwidget.html", 1, ""]]]]
    out = fsi.filter_external(entries)
    assert out == []
    assert fsi.serialize_search_data(out) == "var searchData=[];\n"


# --- AC1.1: mixed multi-result entry keeps only its project child (no doc.qt.io) -----

def test_mixed_children_pruned_keeps_local():
    entries = [["raise_0", ["raise",
                            ["../classAppException.html#a1", 1, "AppException::raise()"],
                            ["https://doc.qt.io/qt-6/qexception.html#raise", 1, "QException"]]]]
    out = fsi.filter_external(entries)
    assert len(out) == 1
    payload = out[0][1]
    assert len(payload) == 2  # pruned down to a single (project) result
    assert payload[1][0] == "../classAppException.html#a1"
    assert payload[1][2] == "AppException::raise()"  # project child's scope preserved
    assert "doc.qt.io" not in fsi.serialize_search_data(out)


# --- AC2.1: brief = first non-definition textblock <p>, tags stripped, re-escaped ----

def test_extract_brief_first_non_definition_p():
    assert fsi.extract_brief(BRIEF_PAGE) == "Some class."


def test_extract_brief_strips_markup_and_reescapes():
    # <a> link dropped (incl. its doc.qt.io href), &amp; round-trips through un/re-escape
    assert fsi.extract_brief(MARKUP_PAGE) == "An exception from Qt &amp; more"


# --- AC2.2: briefless class -> empty scope; definition line never injected -----------

def test_briefless_class_empty_scope():
    brief = fsi.extract_brief(BRIEFLESS_PAGE)
    assert brief == ""
    assert "Definition at line" not in brief
    assert "null" not in brief and "None" not in brief


# --- fail-soft precondition: no textblock raises MissingTextblock --------------------

def test_no_textblock_raises():
    try:
        fsi.extract_brief(NO_TEXTBLOCK_PAGE)
    except fsi.MissingTextblock:
        return
    raise AssertionError("expected MissingTextblock")


# --- AC2.1 end to end: inject brief into a single-result class entry -----------------

def test_inject_single_result_class():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {"classMainWindow.html": BRIEF_PAGE})
        entry = ["mw_0", ["MainWindow", ["../classMainWindow.html", 1, ""]]]
        fsi.inject_brief(entry, search)
        assert entry[1][1][2] == "Some class."


def test_inject_briefless_leaves_empty():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {"classDifferentWindow.html": BRIEFLESS_PAGE})
        entry = ["dw_0", ["DifferentWindow", ["../classDifferentWindow.html", 1, ""]]]
        fsi.inject_brief(entry, search)
        assert entry[1][1][2] == ""  # not "null"/"None", not the definition line


# --- C3: a multi-result entry is left untouched (never write child-0's scope) --------

def test_multi_result_entry_untouched():
    entry = ["foo_0", ["Foo",
                       ["../classFoo.html", 1, "A::Foo"],
                       ["../classFoo.html#m", 1, "B::Foo"]]]
    snapshot = copy.deepcopy(entry)
    fsi.inject_brief(entry, "/nonexistent-dir")  # must not touch the file, must not raise
    assert entry == snapshot


# --- AC2.3: a non-class category file keeps its scopes (no injection) ----------------

def test_non_class_file_scopes_untouched():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {"classAppException.html": BRIEF_PAGE})
        path = os.path.join(search, "functions_0.js")
        content = ("var searchData=\n[\n"
                   "  ['raise_0',['raise',['../classAppException.html#a1',1,"
                   "'AppException::raise()']]]\n];\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        changed = fsi.transform_file(path, search)
        after = open(path, encoding="utf-8").read()
        assert changed is False          # nothing to drop, nothing injected
        assert after == content          # byte-identical: scope untouched


# --- C6: fail-soft - missing page AND no-textblock skipped w/ warning, others done ---

def test_failsoft_skips_bad_entries_and_continues():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {
            "classGood.html": BRIEF_PAGE,
            "classNoBlock.html": NO_TEXTBLOCK_PAGE,
        })
        path = os.path.join(search, "classes_0.js")
        content = ("var searchData=\n[\n"
                   "  ['bad_0',['Bad',['../classMissing.html',1,'']]],\n"
                   "  ['ntb_1',['NoBlock',['../classNoBlock.html',1,'']]],\n"
                   "  ['good_2',['Good',['../classGood.html',1,'']]]\n];\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            fsi.transform_file(path, search)  # must not raise
        out = open(path, encoding="utf-8").read()
        assert "'Some class.'" in out  # the good entry got its brief
        # both bad entries survive with an EMPTY scope (skipped, untouched)
        assert "['bad_0',['Bad',['../classMissing.html',1,'']]]" in out
        assert "['ntb_1',['NoBlock',['../classNoBlock.html',1,'']]]" in out
        warnings = err.getvalue()
        assert warnings.count("WARNING") == 2  # one per skipped entry


# --- impl-review MINOR #1: a backslash in a brief must not break the emitted JS -------
# html.escape(quote=True) covers & < > " ' but NOT '\'; a brief ending in '\' would
# escape the closing single quote and leave that letter file's JS an unterminated string.

def test_serialize_escapes_backslash():
    assert fsi._serialize_node("a\\b") == "'a\\\\b'"        # interior backslash doubled
    assert fsi._serialize_node("trail\\") == "'trail\\\\'"  # trailing backslash no longer escapes the quote
    assert fsi._serialize_node("plain") == "'plain'"        # backslash-free content stays byte-identical


def test_serialize_backslash_round_trips():
    # the emitted entry must re-parse to the original string (idempotent, single-quote form)
    body = "var searchData=\n" + fsi._serialize_node([["x\\y"]]) + ";\n"
    assert fsi.parse_search_data(body) == [["x\\y"]]


# --- impl-review MINOR #2: an anchored (member) URL is skipped silently, no warning ----
# A member-anchored type points into a compound page (`../file_8h.html#structFoo`) whose
# FIRST textblock <p> is the FILE brief, not the type's - resolving it injects a wrong
# excerpt and, un-stripped, the '#...' breaks os.path.isfile -> a per-build WARNING.

def test_class_brief_skips_anchored_url():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {"mainwindow_8h.html": BRIEF_PAGE})
        assert fsi.class_brief(search, "../mainwindow_8h.html#structsomeStruct") == ""


def test_inject_anchored_url_leaves_empty_no_warning():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {"mainwindow_8h.html": BRIEF_PAGE})
        entry = ["ss_0", ["someStruct", ["../mainwindow_8h.html#structsomeStruct", 1, ""]]]
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            fsi.inject_brief(entry, search)  # must not raise, must not warn
        assert entry[1][1][2] == ""              # skipped silently, no wrong file brief
        assert "WARNING" not in err.getvalue()   # anchored types skip quietly


# --- AC3.1: idempotence - transform twice == once -----------------------------------

def test_idempotent_transform():
    with tempfile.TemporaryDirectory() as root:
        search = _mk_pages(root, {"classMainWindow.html": BRIEF_PAGE})
        path = os.path.join(search, "classes_0.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write("var searchData=\n[\n"
                    "  ['mw_0',['MainWindow',['../classMainWindow.html',1,'']]],\n"
                    "  ['qw_1',['QWidget',['https://doc.qt.io/qt-6/qwidget.html',1,'']]]\n];\n")
        fsi.transform_file(path, search)
        after1 = open(path, encoding="utf-8").read()
        changed2 = fsi.transform_file(path, search)
        after2 = open(path, encoding="utf-8").read()
        assert changed2 is False
        assert after2 == after1
        assert "doc.qt.io" not in after1  # external dropped
        assert "'Some class.'" in after1  # brief injected


def test_serializer_is_parser_fixed_point():
    src = "var searchData=\n[\n  ['a_0',['A',['../classA.html',1,'B']]]\n];\n"
    once = fsi.serialize_search_data(fsi.parse_search_data(src))
    twice = fsi.serialize_search_data(fsi.parse_search_data(once))
    assert once == src      # our format reproduces Doxygen's bytes
    assert twice == once    # fixed point -> byte-identical re-runs


def test_parse_rejects_non_searchdata_file():
    assert fsi.parse_search_data("var indexSectionsWithContent =\n{\n  0: \"x\"\n};\n") is None
    assert fsi.parse_search_data("// not search data") is None


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
