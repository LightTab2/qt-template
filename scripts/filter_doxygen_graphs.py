#!/usr/bin/env python3
"""WARNING: vibe coded. Works, but read with suspicion before extending.

Strip std/Boost/Qt nodes from Doxygen collaboration graphs, re-render with graphviz.
Only project types remain. Collaboration graphs (__coll__graph) only; inheritance,
call/caller, include graphs untouched.

Why: BUILTIN_STL_SUPPORT + Qt TAGFILES put library classes in graphs. Settings stay
(accurate signatures, Qt links); graphs get cleaned.

Removed node = contracted, not deleted. Doxygen routes relations through wrappers
(AssetManager -> unordered_map<...> -> AssetImage); deleting wrapper orphans content.
Contraction reconnects kept content straight to kept owner, keeps owner-side member label.

Re-render keeps doxygen interactivity: lift original svg scaffold verbatim, splice in
graphviz's new body. Three svg shapes handled:
  * light interactive  - small graphs: <g id="graph0"> inside <svg id="graph">
  * zoomable           - big graphs: <g id="viewport"> + viewWidth/viewHeight + nav UI
  * _org.svg           - static "open original": <g id="page0,1_graph0">
One .dot backs both X.svg and X_org.svg; filter both or zoom-out shows unfiltered graph.

Shrinking a graph leaves doxygen's referencing <iframe> at its pre-filter box, so the
cleaned diagram renders small inside an oversized frame. So after a graph's SVG pair is
rewritten, this filter also re-syncs every docs/html/*.html iframe that embeds that main
SVG to ceil(pt*4/3) of the SVG's new outer dims (Doxygen 1.17.0's 96-DPI iframe sizing).

Needs DOT_CLEANUP=NO so .dot sources survive next to .svg. Driver: scripts/run_doxygen.sh.

Usage: filter_doxygen_graphs.py <html-dir> [--dot PATH]
Env:   PVN_GRAPH_FILTER_TYPES  comma list of kinds (default "coll"; "inherit" opt-in)
"""

import math
import os
import re
import shutil
import subprocess
import sys

# Known graph kinds. Default: collaboration only. "inherit" opt-in via env.
_KIND_SUFFIX = {"coll": "__coll__graph", "inherit": "__inherit__graph"}

# STL names BUILTIN_STL_SUPPORT synthesises as nodes
_STL_NAMES = (
	"array vector deque list forward_list set multiset map multimap "
	"unordered_set unordered_multiset unordered_map unordered_multimap "
	"stack queue priority_queue pair tuple bitset complex valarray "
	"string wstring u16string u32string basic_string string_view "
	"unique_ptr shared_ptr weak_ptr auto_ptr optional variant any "
	"function reference_wrapper initializer_list span"
).split()
# STL label, with/without std:: prefix; doxygen escapes "<" as "\<"
_STL_RE = re.compile(r'^\s*(?:std::)?(?:' + "|".join(_STL_NAMES) + r')\s*(?:\\?<|$|\s)')

_NODE_RE = re.compile(r'^\s*Node(\d+)\s*\[(.*)\]\s*;\s*$', re.DOTALL)
_EDGE_RE = re.compile(r'^\s*Node(\d+)\s*->\s*Node(\d+)\s*\[(.*)\]\s*;\s*$', re.DOTALL)
_LABEL_RE = re.compile(r'\blabel="((?:[^"\\]|\\.)*)"')
_URL_RE = re.compile(r'\bURL="((?:[^"\\]|\\.)*)"')
_ID_ATTR_RE = re.compile(r'\bid="[^"]*"')

# svg re-render helpers
_OUTER_SVG_RE = re.compile(r'<svg\b[^>]*\bwidth="[0-9.]+pt"[^>]*>', re.DOTALL)
_PLAIN_G0_RE = re.compile(r'<g id="graph0"[^>]*>')
_LIGHT_G_RE = re.compile(r'<g id="[^"]*graph0"[^>]*>')  # graph0 or page0,1_graph0
_VIEWPORT_RE = re.compile(r'<g id="viewport"[^>]*>')
_TRANSFORM_RE = re.compile(r'transform="[^"]*"')
_DIMS_WH_RE = re.compile(r'width="([0-9.]+)pt"\s+height="([0-9.]+)pt"')


def split_statements(text):
	"""Split .dot body into ';'-terminated statements. Honours "quoted" strings and
	<html-like> labels (embed ';' and newlines). Kept statements round-trip byte-for-byte."""
	stmts = []
	buf = []
	in_str = False
	ang = 0  # angle-bracket depth for <<TABLE>...>> html labels
	i = 0
	while i < len(text):
		c = text[i]
		buf.append(c)
		if in_str:
			if c == '\\' and i + 1 < len(text):
				buf.append(text[i + 1])
				i += 2
				continue
			if c == '"':
				in_str = False
		elif c == '"':
			in_str = True
		elif c == '<':
			ang += 1
		elif c == '>':
			if ang > 0:
				ang -= 1
		elif c == ';' and ang == 0:
			stmts.append("".join(buf))
			buf = []
		i += 1
	if "".join(buf).strip():
		stmts.append("".join(buf))
	return stmts


def is_lib_node(attrs):
	"""True = node is std / Boost / Qt, remove from graph."""
	m = _URL_RE.search(attrs)
	if m:
		url = m.group(1)
		if ".tags$" in url or "doc.qt.io" in url:
			return True  # Qt via tag file
		if "boost" in url.lower():
			return True
		return False  # documented project class -> keep
	# No URL: root, STL node, Boost, or undocumented project class
	lm = _LABEL_RE.search(attrs)
	label = lm.group(1) if lm else ""
	if "std::" in label or _STL_RE.match(label):
		return True
	if label.lstrip().startswith("boost::"):
		return True
	return False  # keep root + undocumented project nodes


def filter_dot(text):
	"""Return (new_text, removed_count); (None, 0) if nothing to strip."""
	stmts = split_statements(text)
	node_attrs = {}   # id -> attrs string
	edges = []        # (src, dst, attrs)
	kinds = []        # per-statement: ('raw', text) | ('node', id, text) | ('edge', edge_index)
	for s in stmts:
		em = _EDGE_RE.match(s)
		if em:
			src, dst, attrs = int(em.group(1)), int(em.group(2)), em.group(3)
			kinds.append(('edge', len(edges)))
			edges.append((src, dst, attrs))
			continue
		nm = _NODE_RE.match(s)
		if nm:
			nid = int(nm.group(1))
			node_attrs[nid] = nm.group(2)
			kinds.append(('node', nid, s))
			continue
		kinds.append(('raw', s))

	# Node1 = graph subject (root); never remove
	removed = {nid for nid, a in node_attrs.items() if nid != 1 and is_lib_node(a)}
	if not removed:
		return None, 0

	out_adj = {}  # src -> [(dst, attrs)]
	for src, dst, attrs in edges:
		out_adj.setdefault(src, []).append((dst, attrs))

	def walk_to_kept(start, visited):
		"""Edges point content->owner; walk dst-ward through removed nodes. Return
		(kept_owner, attrs_of_edge_into_owner) - attrs carry owner-side member label."""
		found = []
		for dst, attrs in out_adj.get(start, []):
			if dst in visited:
				continue
			visited.add(dst)
			if dst in removed:
				found.extend(walk_to_kept(dst, visited))
			else:
				found.append((dst, attrs))
		return found

	spliced = []        # (src, dst, attrs)
	seen_pair = set()
	for src, dst, attrs in edges:
		if src in removed:
			continue  # reached instead from its own kept content
		if dst not in removed:
			if (src, dst) not in seen_pair:
				seen_pair.add((src, dst))
				spliced.append((src, dst, attrs))
			continue
		for owner, owner_attrs in walk_to_kept(dst, {dst}):
			if owner == src or (src, owner) in seen_pair:
				continue
			seen_pair.add((src, owner))
			spliced.append((src, owner, owner_attrs))

	out = []
	edge_block_done = False
	idx = [0]

	def fresh_edge(src, dst, attrs):
		# numeric edge<k>_ id keeps svg.min.js highlight parsing working
		idx[0] += 1
		new_id = 'id="edge%d_Node%06d_Node%06d"' % (9000 + idx[0], dst, src)
		if _ID_ATTR_RE.search(attrs):
			attrs = _ID_ATTR_RE.sub(lambda _m: new_id, attrs, count=1)
		else:
			attrs = new_id + "," + attrs
		return "  Node%d -> Node%d [%s];\n" % (src, dst, attrs)

	for k in kinds:
		if k[0] == 'raw':
			out.append(k[1])
		elif k[0] == 'node':
			if k[1] not in removed:
				out.append(k[2])
		else:  # edge: whole edge block replaced by spliced set, in place
			if not edge_block_done:
				edge_block_done = True
				for src, dst, attrs in spliced:
					out.append(fresh_edge(src, dst, attrs))
	return "".join(out), len(removed)


def _matching_g_close(s, pos):
	"""Index of </g> closing the group whose content starts at `pos`."""
	depth = 1
	i = pos
	while i < len(s):
		o = s.find('<g', i)
		c = s.find('</g>', i)
		if c == -1:
			return -1
		if o != -1 and o < c:
			depth += 1
			i = o + 2
		else:
			depth -= 1
			i = c + 4
			if depth == 0:
				return c
	return -1


def rerender_svg(orig_svg, plain_svg):
	"""Splice graphviz's new body into original svg, preserve doxygen scaffold byte-for-byte.
	Handles light-interactive, zoomable, and _org svgs."""
	dims = _OUTER_SVG_RE.search(plain_svg)
	g0 = _PLAIN_G0_RE.search(plain_svg)
	if not dims or not g0:
		return None
	inner_close = _matching_g_close(plain_svg, g0.end())
	if inner_close < 0:
		return None
	new_inner = plain_svg[g0.end():inner_close]
	tm = _TRANSFORM_RE.search(g0.group(0))
	new_transform = tm.group(0) if tm else None

	if 'id="viewport"' in orig_svg:
		# zoomable: swap viewport body, refit JS view box to new size
		vp = _VIEWPORT_RE.search(orig_svg)
		if not vp:
			return None
		b_close = _matching_g_close(orig_svg, vp.end())
		if b_close < 0:
			return None
		out = orig_svg[:vp.end()] + new_inner + orig_svg[b_close:]
		wh = _DIMS_WH_RE.search(dims.group(0))
		if wh:
			w = wh.group(1).split('.')[0]
			h = wh.group(2).split('.')[0]
			out = re.sub(r'var viewWidth = \d+', 'var viewWidth = ' + w, out, count=1)
			out = re.sub(r'var viewHeight = \d+', 'var viewHeight = ' + h, out, count=1)
			out = re.sub(r'<!--zoomable \d+ -->', '<!--zoomable %s -->' % h, out, count=1)
		return out

	# light interactive or _org static: swap outer dims + body transform + body inner
	g = _LIGHT_G_RE.search(orig_svg)
	if not g:
		return None
	b_close = _matching_g_close(orig_svg, g.end())
	if b_close < 0:
		return None
	open_tag = g.group(0)
	if new_transform:
		open_tag = _TRANSFORM_RE.sub(lambda _m: new_transform, open_tag, count=1)
	pre = _OUTER_SVG_RE.sub(lambda _m: dims.group(0), orig_svg[:g.start()], count=1)
	return pre + open_tag + new_inner + orig_svg[b_close:]


def pt_to_px(pt):
	"""Doxygen's SVG-point -> iframe-pixel sizing (96 DPI, round up). Verified against this
	build: 198pt->264, 234pt->312, 164pt->219, 247pt->330, 175pt->234, 287pt->383, 27pt->36.
	Coupled to Doxygen 1.17.0's ceil(pt*4/3) iframe box; a graphviz relayout shifts the SVG's
	pt dims (and hence the px), so px is always DERIVED from the SVG, never a hardcoded table."""
	return math.ceil(float(pt) * 4 / 3)


def rewrite_iframe_html(html_text, svg_basename, w_px, h_px):
	"""Rewrite width/height of every graph <iframe> in html_text that embeds svg_basename.
	Return (new_text, n_replacements). Doxygen 1.17.0 emits the collaboration-graph iframe
	with a FROZEN attribute order src -> width -> height (contract C5); this regex is coupled
	to that 1.17.0 order. Keyed on the exact MAIN-svg basename, so X_org.svg (opened via JS,
	never iframe-embedded) and iframes for other graphs on the same page stay untouched."""
	iframe_re = re.compile(
		r'(src="' + re.escape(svg_basename) + r'"\s+width=")\d+("\s+height=")\d+(")')
	return iframe_re.subn(
		lambda m: m.group(1) + str(w_px) + m.group(2) + str(h_px) + m.group(3), html_text)


def rewrite_iframe_dims(html_dir, svg_basename, w_px, h_px):
	"""Re-sync every html_dir/*.html iframe that embeds svg_basename to (w_px, h_px); return
	the count of HTML files rewritten. A file is written ONLY when its iframe dims actually
	change (n_replacements > 0), so a page that references only untouched graphs stays
	byte-identical (AC6.3) and a second pass over already-synced output is a no-op (AC8.1)."""
	files_changed = 0
	for name in os.listdir(html_dir):
		if not name.endswith(".html"):
			continue
		path = os.path.join(html_dir, name)
		with open(path, encoding="utf-8") as f:
			html_text = f.read()
		new_html, n = rewrite_iframe_html(html_text, svg_basename, w_px, h_px)
		if n:
			with open(path, "w", encoding="utf-8") as f:
				f.write(new_html)
			files_changed += 1
	return files_changed


class GraphFilterError(Exception):
	"""One graph failed to filter/re-render. The caller keeps that graph's ORIGINAL
	Doxygen SVGs and moves on - one bad graph must never abort the whole docs build."""


def process_graph(dot_path, dot_bin):
	"""Filter + re-render ONE graph, atomically. Return (nodes_removed, svg_count) when the
	graph was rewritten, or None when it is skipped untouched (nothing to strip - the
	common case). Raise GraphFilterError on any failure; the caller records ONE failure
	and keeps the originals.

	One .dot backs BOTH X.svg and X_org.svg, so the graph is atomic: both merged bodies
	are built before the first write, and both originals are buffered so a mid-write IO
	failure restores the pair. Either both svgs are rewritten or both stay as Doxygen
	emitted them - never one filtered and its pair original."""
	with open(dot_path, encoding="utf-8") as f:
		text = f.read()
	new_text, n = filter_dot(text)
	if new_text is None:
		return None  # nothing to strip: skipped untouched (the common case, counts as success)
	try:
		plain = subprocess.run(
			[dot_bin, "-Tsvg"], input=new_text, capture_output=True,
			text=True, check=True).stdout
	except subprocess.CalledProcessError as exc:
		raise GraphFilterError("dot -Tsvg failed: %s" % (exc.stderr or exc)) from exc
	# graphviz emits doxygen's URL placeholder verbatim ("$Class.html"), drops link
	# target. Re-rendering bypasses doxygen's own svg post-process, so reapply both:
	# strip $ (else browser follows bogus "$Class.html"), force target=_blank
	plain = plain.replace('xlink:href="$', 'xlink:href="')
	plain = plain.replace('<a xlink:href="', '<a target="_blank" xlink:href="')
	# interactive svg + _org static fallback both render from this dot. Buffer both
	# originals and splice both BEFORE touching disk, so a scaffold-splice failure never
	# leaves one svg filtered and its pair original (the graph is atomic).
	originals = {}     # svg_path -> original bytes, buffered before the first write
	merges = []        # (svg_path, merged) pairs to write once all splices succeed
	for svg_path in (dot_path[:-4] + ".svg", dot_path[:-4] + "_org.svg"):
		if not os.path.exists(svg_path):
			continue
		with open(svg_path, encoding="utf-8") as f:
			orig_svg = f.read()
		originals[svg_path] = orig_svg
		merged = rerender_svg(orig_svg, plain)
		if merged is None:
			raise GraphFilterError("scaffold splice failed: %s" % svg_path)
		merges.append((svg_path, merged))
	if not merges:
		return None  # no sibling svg on disk to rewrite: skipped untouched (counts as success)
	try:
		for svg_path, merged in merges:
			with open(svg_path, "w", encoding="utf-8") as f:
				f.write(merged)
		# Rewritten .dot is left in place BY DESIGN for the driver's `find docs/html -name
		# '*.dot' -delete` (scripts/run_doxygen.sh:105) - do NOT clean it here. Drop .md5
		# so the next incremental doxygen run regenerates this graph (else unchanged
		# checksum skips it, filtered svg stays, no .dot left to re-filter).
		with open(dot_path, "w", encoding="utf-8") as f:
			f.write(new_text)
		md5 = dot_path[:-4] + ".md5"
		if os.path.exists(md5):
			os.remove(md5)
	except Exception as exc:  # noqa: BLE001 - restore the pair, then surface as one failure
		# A write itself failed mid-graph: write both buffered originals back so the pair
		# stays consistent, then let the caller record one failure and continue. Each restore
		# write is itself guarded: the same condition that failed the original write (disk full,
		# read-only fs) can fail the restore too, and a truncated svg must be NAMED, not silently
		# claimed "restored".
		unrestored = []
		for svg_path, orig_svg in originals.items():
			try:
				with open(svg_path, "w", encoding="utf-8") as f:
					f.write(orig_svg)
			except OSError as restore_exc:
				unrestored.append("%s (%s)" % (svg_path, restore_exc))
		if unrestored:
			raise GraphFilterError(
				"write failed: %s; COULD NOT restore: %s" % (exc, "; ".join(unrestored))) from exc
		raise GraphFilterError("write failed, originals restored: %s" % exc) from exc
	# FC01.4 / R6-R8: the SVG pair is rewritten and (for the light-interactive shape) shrunk,
	# but doxygen's referencing <iframe> still carries the pre-filter box, so the cleaned
	# diagram renders small in an oversized frame. Re-sync every docs/html/*.html iframe that
	# embeds THIS graph's MAIN svg to ceil(pt*4/3) of the rewritten SVG's OWN outer <svg> dims
	# (read from the merged main svg, not graphviz's plain output: a zoomable graph keeps its
	# fixed outer window, so its iframe must stay put). Runs ONLY here on the per-graph success
	# path - every failure above raised and returned via the caller's guard - so the fixup
	# inherits the filter's per-graph fail-soft: a graph whose rewrite failed never reaches it
	# and its iframe is left untouched (AC8.2).
	iframes = 0
	main_svg = dot_path[:-4] + ".svg"
	main_merged = next((m for p, m in merges if p == main_svg), None)
	if main_merged is not None:
		wh = _DIMS_WH_RE.search(main_merged)
		if wh:
			iframes = rewrite_iframe_dims(
				os.path.dirname(dot_path), os.path.basename(main_svg),
				pt_to_px(wh.group(1)), pt_to_px(wh.group(2)))
	return n, len(merges), iframes


def process(html_dir, dot_bin):
	kinds = os.environ.get("PVN_GRAPH_FILTER_TYPES", "coll").split(",")
	suffixes = [_KIND_SUFFIX[k.strip()] for k in kinds if k.strip() in _KIND_SUFFIX]
	dots = sorted(
		os.path.join(html_dir, n) for n in os.listdir(html_dir)
		if n.endswith(".dot") and any(n.endswith(s + ".dot") for s in suffixes))

	scanned = changed = skipped = nodes_removed = svg_done = iframes_updated = 0
	failures = []
	for dot_path in dots:
		scanned += 1
		try:
			result = process_graph(dot_path, dot_bin)
		except Exception as exc:  # noqa: BLE001 - one bad graph must not kill the docs build
			# Per-graph fail-soft: warn (naming the graph), keep BOTH original SVGs (left
			# untouched, or restored in process_graph on a mid-write failure), count ONE
			# failure, and continue. No `finally`/success-path cleanup: successfully
			# rewritten .dot files must survive for the driver's find -delete.
			failures.append(dot_path)
			sys.stderr.write(
				"[graph-filter] WARNING: graph filter failed for %s: %s; kept original SVGs\n"
				% (dot_path, exc))
			continue
		if result is None:
			skipped += 1
			continue
		n, wrote, iframes = result
		changed += 1
		nodes_removed += n
		svg_done += wrote
		iframes_updated += iframes

	print("[graph-filter] %d graphs scanned, %d svg rewritten, %d lib nodes removed, "
		"%d iframes re-synced; filtered %d graphs, %d failed (originals kept)"
		% (scanned, svg_done, nodes_removed, iframes_updated, changed, len(failures)))
	# Exit 0 when >=1 graph succeeded or was skipped, or when there were zero graphs; a
	# skip (filter_dot -> None, the common case) counts as SUCCESS. Exit 1 ONLY when every
	# graph failed (>=1 failure and zero successes/skips) - setup failures are in main().
	return 1 if (failures and (changed + skipped) == 0) else 0


def main(argv):
	if len(argv) < 2 or argv[1] in ("-h", "--help"):
		sys.stderr.write(__doc__)
		return 2
	html_dir = argv[1]
	dot_bin = None
	if "--dot" in argv:
		dot_bin = argv[argv.index("--dot") + 1]
	dot_bin = dot_bin or os.environ.get("DOT") or shutil.which("dot")
	if not dot_bin:
		sys.stderr.write("[graph-filter] graphviz 'dot' not found\n")
		return 1
	if not os.path.isdir(html_dir):
		sys.stderr.write("[graph-filter] not a directory: %s\n" % html_dir)
		return 1
	return process(html_dir, dot_bin)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
