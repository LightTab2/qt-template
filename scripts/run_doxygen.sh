#!/usr/bin/env bash
# WARNING: vibe coded. Works, but read with suspicion before extending.
#
# Doxygen build entry point. Offline after first run.
# Single source of truth: pinned doxygen version (DOXY_VER), Qt modules (MODULES),
# config (CONFIG). Pins doxygen 1.17.0, never tracks "latest". First run fetches
# binary + Qt tag files into caches (theme vendored in-tree); later runs offline.
# CI counterpart: .github/workflows/doxygen.yml (builds and publishes docs/html on push to main).
set -euo pipefail

# Repo root, regardless of call site.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# --- config (single source of versions/paths) ---
DOXY_VER=1.17.0
CACHE_DIR="$REPO_ROOT/.doxygen-bin/$DOXY_VER"
DOXY_HOME="$CACHE_DIR/doxygen-$DOXY_VER"
CONFIG=doxygen/Doxyfile_dev
TAGS_DIR=doxygen/qt-tags
MODULES="qtcore qtgui qtwidgets"
# Caller may pre-set DOXYGEN_BIN; default = cached pinned binary.
DOXYGEN_BIN="${DOXYGEN_BIN:-$DOXY_HOME/bin/doxygen}"

# True when $1 exists and reports exactly DOXY_VER.
doxy_is_pinned() {
	local bin="$1"
	[ -x "$bin" ] || return 1
	case "$("$bin" --version 2>/dev/null)" in
		"$DOXY_VER"*)
			return 0
			;;
		*)
			return 1
			;;
	esac
}

# --- 1. pinned doxygen 1.17.0 (cache once, reuse; never resolve "latest") ---
# System doxygen 1.9.x has type-token bug: void/const/int/virtual... cross-resolve to
# global *_cast tag entries, keywords render as <a> links, lose keyword coloring.
if doxy_is_pinned "$DOXYGEN_BIN"; then
	echo "==> doxygen $DOXY_VER present ($DOXYGEN_BIN)"
elif command -v doxygen >/dev/null 2>&1 && doxy_is_pinned "$(command -v doxygen)"; then
	DOXYGEN_BIN="$(command -v doxygen)"
	echo "==> using system doxygen $DOXY_VER"
else
	if [ ! -x "$DOXY_HOME/bin/doxygen" ]; then
		PRIMARY="https://www.doxygen.nl/files/doxygen-$DOXY_VER.linux.bin.tar.gz"
		FALLBACK="https://github.com/doxygen/doxygen/releases/download/Release_${DOXY_VER//./_}/doxygen-$DOXY_VER.linux.bin.tar.gz"
		TGZ="$CACHE_DIR/doxygen-$DOXY_VER.linux.bin.tar.gz"
		mkdir -p "$CACHE_DIR"
		echo "==> Fetching pinned doxygen $DOXY_VER (one-time; system has $(doxygen --version 2>/dev/null || echo none))"
		if ! curl -sSfL --retry 3 -o "$TGZ" "$PRIMARY" && ! curl -sSfL --retry 3 -o "$TGZ" "$FALLBACK"; then
			echo "==> ERROR: doxygen $DOXY_VER missing and download failed (offline?); run once online or set DOXYGEN_BIN to a $DOXY_VER binary" >&2
			exit 1
		fi
		tar -xzf "$TGZ" -C "$CACHE_DIR"
		rm -f "$TGZ"
		chmod +x "$DOXY_HOME/bin/doxygen" 2>/dev/null || true
	fi
	DOXYGEN_BIN="$DOXY_HOME/bin/doxygen"
	if ! doxy_is_pinned "$DOXYGEN_BIN"; then
		echo "==> ERROR: expected doxygen $DOXY_VER at $DOXYGEN_BIN but got $("$DOXYGEN_BIN" --version 2>/dev/null)" >&2
		exit 1
	fi
fi

# --- 2. graphviz check (Doxyfile sets HAVE_DOT=YES) ---
if ! command -v dot >/dev/null 2>&1; then
	echo "==> ERROR: graphviz 'dot' not found (apt install graphviz)" >&2
	exit 1
fi

# --- 3. theme presence check (vendored, not a submodule) ---
if [ ! -f doxygen-style-revamped/doxygen-style-revamped-theme.css ]; then
	echo "==> ERROR: doxygen-style-revamped theme missing (expected doxygen-style-revamped/doxygen-style-revamped-theme.css)" >&2
	exit 1
fi
echo "==> doxygen-style-revamped present"

# --- 4. Qt tag files (gitignored local cache; fetched on demand if missing, never fail offline) ---
for m in $MODULES; do
	if [ ! -s "$TAGS_DIR/$m/$m.tags" ]; then
		mkdir -p "$TAGS_DIR/$m"
		echo "==> Fetching Qt tags: $m"
		if ! curl -sSfL --retry 3 "https://doc.qt.io/qt-6/$m.tags" -o "$TAGS_DIR/$m/$m.tags"; then
			rm -f "$TAGS_DIR/$m/$m.tags"
			echo "==> WARN: Qt tag links for $m skipped (offline, no cache)" >&2
		fi
	fi
done
export QT_TAGS="$REPO_ROOT/$TAGS_DIR"

# --- 5. build (output dir set by Doxyfile_dev: OUTPUT_DIRECTORY=docs) ---
echo "==> Running doxygen ($("$DOXYGEN_BIN" --version)) on $CONFIG"

# --- 5.0 theme JS feature gating (DSR_* toggles, contract C2) ---
# Each DSR_* var gates exactly one vendored theme script; semantics match
# PVN_GRAPH_FILTER (${VAR:-1} != "0" means on, unset = on). The feature->filename
# mapping below is FROZEN (feature 03 keys each script to its DSR_* var). DSR_JS=0 is
# master-off: drop every feature script AND vendored jQuery. Gating is SUBTRACTIVE and
# applied ONLY here: the committed header.html + Doxyfile HTML_EXTRA_FILES list jQuery
# plus all eight scripts (all-on default), so a raw `doxygen doxygen/Doxyfile_dev` run
# (no script) still emits every feature (R12). Here we strip disabled scripts from a
# temp header and override HTML_HEADER / HTML_EXTRA_FILES via the piped config below.
# Markup shapes and $relpath^ names are Doxygen 1.17.0 specific.
THEME_DIR="doxygen-style-revamped"
JQUERY_FILE="$THEME_DIR/doxygen-style-revamped-jquery.js"
# Ordered "ENV_VAR:basename" pairs (source order matches header.html).
DSR_FEATURES="
DSR_DARKMODE:doxygen-style-revamped-darkmode-toggle.js
DSR_BADGES:doxygen-style-revamped-badges.js
DSR_CODE_PUNCT:doxygen-style-revamped-code-punct.js
DSR_INHERITED:doxygen-style-revamped-inherited-toggle.js
DSR_KEYWORDS:doxygen-style-revamped-keywords.js
DSR_COLORMEMBERS:doxygen-style-revamped-colormembers.js
DSR_PERMALINK:doxygen-style-revamped-permalink.js
DSR_RESIZE:doxygen-style-revamped-resize.js
"
HDR_TMP="$(mktemp)"
trap 'rm -f "$HDR_TMP"' EXIT
cp "$THEME_DIR/header.html" "$HDR_TMP"
ENABLED_FILES=""      # space-joined theme JS paths for the HTML_EXTRA_FILES override
DISABLED_NAMES=""     # basenames dropped, for the progress line
ENABLED_COUNT=0
for feat in $DSR_FEATURES; do
	dsr_var="${feat%%:*}"
	dsr_file="${feat#*:}"
	if [ "${DSR_JS:-1}" = "0" ] || [ "${!dsr_var:-1}" = "0" ]; then
		# Disabled: strip its <script> line from the temp header (and never copy it).
		sed -i "\%$dsr_file%d" "$HDR_TMP"
		DISABLED_NAMES="$DISABLED_NAMES $dsr_file"
	else
		ENABLED_FILES="$ENABLED_FILES $THEME_DIR/$dsr_file"
		ENABLED_COUNT=$((ENABLED_COUNT + 1))
	fi
done
# C1: jQuery is emitted iff at least one feature is enabled, and always first.
if [ "$ENABLED_COUNT" -eq 0 ]; then
	sed -i "\%doxygen-style-revamped-jquery.js%d" "$HDR_TMP"
	EXTRA_FILES=""
else
	EXTRA_FILES="$JQUERY_FILE$ENABLED_FILES"
fi
if [ -n "$DISABLED_NAMES" ]; then
	echo "==> Theme JS: $ENABLED_COUNT enabled (disabled:$DISABLED_NAMES)"
else
	echo "==> Theme JS: $ENABLED_COUNT enabled (disabled: none)"
fi
# Override HTML_HEADER (gated temp copy) + HTML_EXTRA_FILES (a repeated list tag
# REPLACES in doxygen; the base list is JS-only, so "jQuery + enabled" is the complete
# set). CSS/fonts live in HTML_EXTRA_STYLESHEET and are untouched.
OVERRIDES="$(printf '\nHTML_HEADER = %s\nHTML_EXTRA_FILES = %s\n' "$HDR_TMP" "$EXTRA_FILES")"

# PVN_GRAPH_FILTER (default on): drop std/Boost/Qt nodes from collaboration graphs,
# re-render those. DOT_CLEANUP=NO keeps .dot sources graphviz needs; deleted after
# so output matches a normal DOT_CLEANUP=YES build. Both branches pipe the config
# through stdin so the gating overrides above apply (FC01.1).
if [ "${PVN_GRAPH_FILTER:-1}" != "0" ]; then
	echo "==> Graph filter on (PVN_GRAPH_FILTER=0 to disable)"
	( cat "$CONFIG"; printf '%s' "$OVERRIDES"; printf '\nDOT_CLEANUP = NO\n' ) | "$DOXYGEN_BIN" -
	python3 "$SCRIPT_DIR/filter_doxygen_graphs.py" docs/html
	find docs/html -name '*.dot' -delete
else
	( cat "$CONFIG"; printf '%s\n' "$OVERRIDES" ) | "$DOXYGEN_BIN" -
fi

# --- 5.5 search-index post-processor (PVN_SEARCH_FILTER, default on; PVN_GRAPH_FILTER
# semantics, ${VAR:-1} != "0" means on). Rewrites the generated client-side search index
# docs/html/search/*.js: drop external (Qt tag-file) results so only project-authored
# symbols remain, and inject each surviving project class's brief as its result excerpt
# (span.SRScope, contract C3). Reads only already-generated HTML - offline, idempotent,
# and fail-soft (a bad/absent class page warns to stderr and is skipped, never aborts the
# build). Runs AFTER the build block; task-04 appends its own step after this one.
if [ "${PVN_SEARCH_FILTER:-1}" != "0" ]; then
	echo "==> Filtering search index (drop external symbols, inject class excerpts)"
	python3 "$SCRIPT_DIR/filter_search_index.py" docs/html/search
fi

# --- 5.6 declaration-line restore (PVN_RESTORE_DEFLINE, default on; PVN_GRAPH_FILTER
# semantics, ${VAR:-1} != "0" means on). With INLINE_SOURCES=YES + SOURCE_BROWSER=YES,
# Doxygen starts each member-detail inline-source fragment at the line AFTER the declaration,
# so a member "Definition at line N" renders starting at N+1 (its body). This rewrites
# docs/html/*.html (skipping *_source.html): for each such fragment it prepends the rendered
# source lines N..F1-1 pulled from the already-generated F_source.html page (leading per-line
# anchors stripped), so the fragment begins at line N. Reads only generated HTML - offline,
# idempotent (after a splice F1==N so the guard is false on re-run), and fail-soft (a missing
# source page / inconsistent definition / out-of-range line warns to stderr and is skipped,
# never aborts the build). Runs AFTER the search-filter step; markup shapes are Doxygen 1.17.0
# specific.
if [ "${PVN_RESTORE_DEFLINE:-1}" != "0" ]; then
	echo "==> Restoring declaration line in inline-source fragments"
	python3 "$SCRIPT_DIR/restore_definition_line.py" docs/html
fi

# --- 5a. graph links open new window. Doxygen targets graph node links at doc frame
# (target="_parent"/"_top"): clicking a class in a graph replaces current page. Rewrite
# to _blank. Filtered collaboration graphs already _blank (filter_doxygen_graphs.py);
# this catches native graphs.
echo "==> Forcing graph links to open in a new window (target=_blank)"
find docs/html -maxdepth 1 -name '*graph*.svg' -print0 | xargs -0 -r perl -i -pe 's/target="(?:_parent|_top)"/target="_blank"/g'

# --- 5b. pointer/reference spacing: repo uses east style (Type* name), doxygen always
# emits west (Type *name). Rewrite generated declaration markup only - member/param/
# return cells, member-index entries. Per-line gate keeps operators (*deref, &addr) in
# code fragments, prose, and *_source.html intact (e.g. "return *this" in \code).
echo "==> Normalizing pointer/reference spacing in generated HTML"
find docs/html -maxdepth 1 -name '*.html' ! -name '*_source.html' -print0 | xargs -0 -r perl -i -pe '
	if (/class="(?:memItemRight|memItemLeft|paramtype|paramname|memname|entry|memTemplItemLeft|memTemplItemRight)"/) {
		s{(</a>|&gt;|[A-Za-z0-9_]) ((?:\*|&amp;)+)(?=[A-Za-z_])}{$1$2 }g;
		s{(</a>|&gt;|[A-Za-z0-9_]) ((?:\*|&amp;)+)(?=[\),=.<]|&#160;)}{$1$2}g;
	}
'

# --- 6. copy webfonts. Doxygen flattens HTML_EXTRA_STYLESHEET/_FILES into docs/html,
# ignores directory entries, never copies @font-face binaries under fonts/. Without
# this: woff2 404s, browser falls back to system fonts. Mirror dir so
# url('fonts/...') resolves.
echo "==> Copying webfonts to docs/html/fonts"
rm -rf docs/html/fonts && mkdir -p docs/html/fonts
cp doxygen-style-revamped/fonts/*.{eot,woff2,woff,ttf,svg} docs/html/fonts/ 2>/dev/null || true

echo "==> Done. Open docs/html/index.html"
