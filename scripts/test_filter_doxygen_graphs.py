#!/usr/bin/env python3
"""Standalone python3-assert tests for scripts/filter_doxygen_graphs.py (no pytest).

Covers the iframe re-sync added onto the graph filter's per-graph success path:
  * R7 / AC7.1 - pt_to_px reproduces Doxygen 1.17.0's 96-DPI ceil(pt*4/3) sizing, for
    every real SVG-pt -> iframe-px pair captured from a build.
  * R6 / AC6.3 - the iframe rewrite touches ONLY the iframe pointing at the targeted main
    SVG; other iframes on the page and pages that reference untouched graphs stay
    byte-identical; a non-matching basename is a no-op (count 0).
  * R8 / AC8.1 - the rewrite is idempotent (running it twice == once, byte-identical).
  * R8 / AC8.2 - fail-soft: when a graph's SVG rewrite fails, process_graph raises before
    the fixup, so the referencing iframe is left untouched.

Run: python3 scripts/test_filter_doxygen_graphs.py
"""

import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import filter_doxygen_graphs as fdg  # noqa: E402


# Real Doxygen 1.17.0 collaboration-graph iframe markup (contract C5): the frozen
# attribute order is src -> width -> height. Two graphs on one page.
TWO_IFRAMES = (
	'<div class="center"><iframe scrolling="no" loading="lazy" frameborder="0" '
	'src="classMainWindow__coll__graph.svg" width="219" height="256">'
	'<p><b>This browser is not able to show SVG: try Firefox, Chrome, Safari, '
	'or Opera instead.</b></p></iframe></div>\n'
	'<div class="center"><iframe scrolling="no" loading="lazy" frameborder="0" '
	'src="classAppException__coll__graph.svg" width="163" height="256">'
	'</iframe></div>\n'
)

# A minimal .dot with a removable std:: lib node, so filter_dot returns non-None and
# process_graph proceeds to the (here forced-to-fail) SVG rewrite. Statements before the
# first Node end with ';' so the Node statements start clean for _NODE_RE.
DOT_WITH_LIB_NODE = (
	'digraph "X"\n'
	'{\n'
	'  bgcolor="transparent";\n'
	'  edge [fontname=Helvetica];\n'
	'  node [fontname=Helvetica];\n'
	'  Node1 [id="Node000001",label="X",height=0.2,width=0.4,color="grey40"];\n'
	'  Node2 [id="Node000002",label="std::vector\\< int \\>",height=0.2,width=0.4];\n'
	'  Node2 -> Node1 [id="edge1_Node000002_Node000001",dir="back",color="steelblue1"];\n'
	'}\n'
)

# Doxygen 1.17.0 light-interactive collaboration svg BEFORE filtering: an oversized 219x256pt
# outer box with a <g id="graph0"> scaffold (no id="viewport" -> rerender_svg's light path).
ORIG_LIGHT_SVG = (
	'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
	'<svg width="219pt" height="256pt" viewBox="0.00 0.00 219.00 256.00" '
	'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
	'<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 252)">\n'
	'<title>X</title>\n'
	'<polygon fill="white" points="-4,4 -4,-252 215,-252 215,4 -4,4"/>\n'
	'<!-- stale pre-filter body: the std::vector node still here -->\n'
	'</g>\n'
	'</svg>\n'
)

# What the fake `dot -Tsvg` emits for the FILTERED graph: a valid graphviz plain svg, now
# SHRUNK to 118x36pt. rerender_svg splices this body into ORIG_LIGHT_SVG and swaps the outer
# dims, so the merged main svg's own outer box (and hence the iframe) becomes 118x36pt.
PLAIN_SHRUNK_SVG = (
	'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
	'<svg width="118pt" height="36pt" viewBox="0.00 0.00 118.00 36.00" '
	'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
	'<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(4 32)">\n'
	'<title>X</title>\n'
	'<polygon fill="transparent" points="-4,4 -4,-32 114,-32 114,4 -4,4"/>\n'
	'</g>\n'
	'</svg>\n'
)


def test_pt_to_px_ac7_1():
	"""AC7.1: every captured SVG-pt -> iframe-px pair, exact-divisible and round-up."""
	pairs = {198: 264, 234: 312, 164: 219, 247: 330, 175: 234, 287: 383, 27: 36}
	for pt, px in pairs.items():
		got = fdg.pt_to_px(pt)
		assert got == px, "pt_to_px(%d) == %d, want %d" % (pt, got, px)
	# also accepts the string groups _DIMS_WH_RE yields, and fractional pt dims
	assert fdg.pt_to_px("164") == 219, "pt_to_px accepts str"
	assert fdg.pt_to_px("88.5") == 118, "pt_to_px accepts fractional pt"


def test_rewrite_iframe_html_targeted():
	"""AC6.3: only the targeted src's width/height change; the sibling iframe is untouched."""
	new, n = fdg.rewrite_iframe_html(TWO_IFRAMES, "classMainWindow__coll__graph.svg", 118, 36)
	assert n == 1, "exactly one iframe rewritten, got %d" % n
	assert 'src="classMainWindow__coll__graph.svg" width="118" height="36"' in new, \
		"targeted iframe not resized"
	assert 'src="classAppException__coll__graph.svg" width="163" height="256"' in new, \
		"sibling iframe must stay untouched"


def test_rewrite_iframe_html_no_match():
	"""AC6.3: a basename that no iframe references is a no-op (count 0, text unchanged)."""
	same, n = fdg.rewrite_iframe_html(TWO_IFRAMES, "classNope__coll__graph.svg", 10, 10)
	assert n == 0, "no-match count must be 0, got %d" % n
	assert same == TWO_IFRAMES, "no-match must return the text unchanged"


def test_rewrite_iframe_html_ignores_org_svg():
	"""The main-svg basename must NOT match the JS-only X_org.svg iframe/link, if present."""
	org = ('<a href="classMainWindow__coll__graph_org.svg">original</a>\n'
		'<iframe src="classMainWindow__coll__graph_org.svg" width="219" height="256"></iframe>\n')
	same, n = fdg.rewrite_iframe_html(org, "classMainWindow__coll__graph.svg", 118, 36)
	assert n == 0, "must not touch *_org.svg, got %d" % n
	assert same == org


def test_rewrite_iframe_html_idempotent():
	"""AC8.1: rewriting twice == once (byte-identical)."""
	once, _ = fdg.rewrite_iframe_html(TWO_IFRAMES, "classMainWindow__coll__graph.svg", 118, 36)
	twice, n2 = fdg.rewrite_iframe_html(once, "classMainWindow__coll__graph.svg", 118, 36)
	assert twice == once, "second pass must be byte-identical to the first"


def _read(path):
	with io.open(path, encoding="utf-8") as f:
		return f.read()


def test_rewrite_iframe_dims_files():
	"""AC6.3 at file level: rewrite the referencing page, leave the other page and non-HTML
	files byte-identical; report one file changed; re-run byte-identical (AC8.1)."""
	with tempfile.TemporaryDirectory() as d:
		target = os.path.join(d, "classMainWindow.html")
		other = os.path.join(d, "classAppException.html")
		txt = os.path.join(d, "readme.txt")
		target_html = ('<iframe src="classMainWindow__coll__graph.svg" '
			'width="219" height="256"></iframe>\n')
		other_html = ('<iframe src="classAppException__coll__graph.svg" '
			'width="163" height="256"></iframe>\n')
		txt_body = 'src="classMainWindow__coll__graph.svg" width="219" height="256"\n'
		for path, body in ((target, target_html), (other, other_html), (txt, txt_body)):
			with io.open(path, "w", encoding="utf-8") as f:
				f.write(body)
		changed = fdg.rewrite_iframe_dims(d, "classMainWindow__coll__graph.svg", 118, 36)
		assert changed == 1, "exactly one HTML file rewritten, got %d" % changed
		assert 'width="118" height="36"' in _read(target), "target not resized"
		assert _read(other) == other_html, "AC6.3: untouched-graph page must be byte-identical"
		assert _read(txt) == txt_body, "non-HTML file must be ignored"
		# AC8.1 file-level idempotence: a second pass leaves the target byte-identical.
		after1 = _read(target)
		fdg.rewrite_iframe_dims(d, "classMainWindow__coll__graph.svg", 118, 36)
		assert _read(target) == after1, "AC8.1: re-run must be byte-identical"


def test_failsoft_leaves_iframe_untouched():
	"""AC8.2: a graph whose SVG rewrite FAILS -> process_graph raises before the fixup, so
	the referencing iframe is left untouched (the fixup runs only on the success path)."""
	with tempfile.TemporaryDirectory() as d:
		dot = os.path.join(d, "classX__coll__graph.dot")
		with io.open(dot, "w", encoding="utf-8") as f:
			f.write(DOT_WITH_LIB_NODE)
		html = os.path.join(d, "classX.html")
		original = ('<div class="center"><iframe scrolling="no" loading="lazy" '
			'frameborder="0" src="classX__coll__graph.svg" width="219" height="256">'
			'</iframe></div>\n')
		with io.open(html, "w", encoding="utf-8") as f:
			f.write(original)
		# a "dot" that always exits non-zero: the SVG rewrite fails -> GraphFilterError,
		# returning BEFORE the iframe fixup (the per-graph fail-soft path).
		fake_dot = os.path.join(d, "fake_dot")
		with io.open(fake_dot, "w", encoding="utf-8") as f:
			f.write("#!/bin/sh\nexit 1\n")
		os.chmod(fake_dot, 0o755)
		raised = False
		try:
			fdg.process_graph(dot, fake_dot)
		except fdg.GraphFilterError:
			raised = True
		assert raised, "expected GraphFilterError on the fail-soft path"
		assert _read(html) == original, \
			"AC8.2: iframe must be byte-identical after a failed SVG rewrite"


def test_process_graph_success_resyncs_iframe():
	"""R6/FC01.4 SUCCESS-path wiring: a graph that IS filtered re-renders its SVG pair and
	process_graph resyncs the referencing iframe to ceil(pt*4/3) of the rewritten main SVG's
	OWN outer dims. The unit suite otherwise only proved the helpers and the FAILURE path
	(AC8.2); this drives the whole success path with a fake dot emitting a valid shrunk SVG."""
	with tempfile.TemporaryDirectory() as d:
		dot = os.path.join(d, "classMainWindow__coll__graph.dot")
		with io.open(dot, "w", encoding="utf-8") as f:
			f.write(DOT_WITH_LIB_NODE)
		# the original doxygen light-interactive svg (pre-filter, oversized 219x256pt)
		svg = os.path.join(d, "classMainWindow__coll__graph.svg")
		with io.open(svg, "w", encoding="utf-8") as f:
			f.write(ORIG_LIGHT_SVG)
		# doxygen's referencing iframe still carries the stale pre-filter 219x256 box
		html = os.path.join(d, "classMainWindow.html")
		with io.open(html, "w", encoding="utf-8") as f:
			f.write('<div class="center"><iframe scrolling="no" loading="lazy" '
				'frameborder="0" src="classMainWindow__coll__graph.svg" '
				'width="219" height="256"></iframe></div>\n')
		# a fake "dot" that emits the valid SHRUNK plain svg (118x36pt) on -Tsvg, exit 0
		fake_dot = os.path.join(d, "fake_dot")
		with io.open(fake_dot, "w", encoding="utf-8") as f:
			f.write("#!/bin/sh\ncat <<'SVGEOF'\n" + PLAIN_SHRUNK_SVG + "SVGEOF\n")
		os.chmod(fake_dot, 0o755)

		result = fdg.process_graph(dot, fake_dot)
		assert result is not None, "a filtered graph must return a result, not skip"
		n, svg_count, iframes = result
		assert iframes == 1, "the referencing iframe must be resynced, got %d" % iframes
		# 118pt -> ceil(118*4/3)=158 ; 36pt -> ceil(36*4/3)=48, both DERIVED from the svg
		assert 'src="classMainWindow__coll__graph.svg" width="158" height="48"' in _read(html), \
			"iframe dims must derive from the rewritten svg's own outer dims"
		assert 'width="118pt" height="36pt"' in _read(svg), \
			"the rewritten main svg must carry the new shrunk outer dims"


def main():
	tests = [
		test_pt_to_px_ac7_1,
		test_rewrite_iframe_html_targeted,
		test_rewrite_iframe_html_no_match,
		test_rewrite_iframe_html_ignores_org_svg,
		test_rewrite_iframe_html_idempotent,
		test_rewrite_iframe_dims_files,
		test_failsoft_leaves_iframe_untouched,
		test_process_graph_success_resyncs_iframe,
	]
	for t in tests:
		t()
		print("ok  %s" % t.__name__)
	print("all %d filter_doxygen_graphs tests passed" % len(tests))
	return 0


if __name__ == "__main__":
	sys.exit(main())
