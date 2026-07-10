# Documentation pipeline (Doxygen) - analysis

## Purpose

This subsystem turns the C++/Qt6 template's source and Markdown pages into a
self-contained, reproducible Doxygen HTML site under `docs/html`. It solves three
problems the stock Doxygen path does not: (1) build determinism - it pins **Doxygen
1.17.0** and caches it offline so output never drifts with whatever `doxygen` the host
happens to ship; (2) Qt integration - it fetches Qt tag files so project symbols
cross-link to `doc.qt.io`, and it applies a vendored Qt-6-styled theme
(`doxygen-style-revamped`) whose feature scripts run on vendored **jQuery 3.7.1** and are
each build-time gateable via `DSR_*` toggles; and (3) output polish - a chain of
post-processors that clean library noise out of collaboration graphs, filter the
client-side search index (drop external symbols, inject class excerpts), restore dropped
declaration lines in inline-source fragments, re-sync filtered graph iframes to their
shrunk SVGs, normalize pointer/reference spacing, force graph links to open in new tabs,
and copy webfont binaries the theme CSS needs; generated/external namespaces (`Ui`,
`std`, `boost`, `gsl`) are excluded from the docs via `EXCLUDE_SYMBOLS`. The whole thing
is offline after the first run and is driven by one entry-point script,
`scripts/run_doxygen.sh`.

## Owned paths

Globs this domain owns outright (source + config + generated artifacts):

- `doxygen/**` - `Doxyfile`, `Doxyfile_dev`, `header.html`,
  `footer.html`, `layout.xml`, `qt-tags/**` (Qt tag-file cache; gitignored).
- `scripts/run_doxygen.sh`, `scripts/serve_doxygen.sh`, `scripts/filter_doxygen_graphs.py`,
  `scripts/filter_search_index.py`, `scripts/restore_definition_line.py`,
  `scripts/test_filter_search_index.py`, `scripts/test_restore_definition_line.py`,
  `scripts/test_filter_doxygen_graphs.py`, `scripts/__pycache__/**` (the entire `scripts/`
  directory is docs-only in this repo).
- `doxygen-style-revamped/**` - vendored Doxygen theme (CSS + jQuery-based feature JS +
  vendored `doxygen-style-revamped-jquery.js` + fonts).
- `.doxygen-bin/**` - pinned Doxygen 1.17.0 binary cache (gitignored).
- `docs/**` - generated HTML output (gitignored).
- `pages/**` - documentation source pages and images (`index.md` mainpage, `Test.md`,
  `*.png`).

Shared paths (NOT exclusively owned - flag for coordination):

- `Makefile` - the `docs`, `docs-serve`, `docs-clean` targets (lines 32-39) belong to this
  domain, but the file is shared with the build/deps domain (`configure`, `build`, `test`,
  etc.).
- `.github/workflows/doxygen.yml` - CI docs build/deploy belongs here, but the
  `.github/workflows/` tree is shared with the CI domain.
- `CLAUDE.md` and `README.md` - both carry a Documentation section owned by this domain but
  the files are shared repo-wide.
- `src/**` and `pages/**` are the Doxygen `INPUT`; `src/**` is owned by the app/library
  domain (this domain only reads it and depends on its `/// \brief` doc-comment style).

## Key files & symbols

| File | Central symbols / config | One line |
| --- | --- | --- |
| `scripts/run_doxygen.sh` | `doxy_is_pinned()`, steps 1-6, `DOXY_VER`, `CONFIG`, `MODULES`, `QT_TAGS`, `DSR_*` gating | The single docs entry point: resolve pinned binary, fetch Qt tags, emit jQuery-first + DSR-gated theme scripts, run Doxygen, post-process (graph filter, search filter, decl-line restore), copy fonts. |
| `scripts/filter_doxygen_graphs.py` | `split_statements`, `is_lib_node`, `filter_dot`, `walk_to_kept`, `fresh_edge`, `rerender_svg`, `_matching_g_close`, `pt_to_px`, `process_graph`, `process`, `main`, `GraphFilterError` | Strips std/Boost/Qt nodes from collaboration graphs by node-contraction, re-renders SVG in place, and re-syncs each filtered graph's iframe `width`/`height` to the shrunk SVG (`ceil(pt*4/3)`) on `process_graph`'s success path; per-graph fail-soft. |
| `scripts/filter_search_index.py` | `is_external`, class-excerpt injection, `main(dir)` | Search-index post-processor: drops external (`http(s)://`) symbols from `docs/html/search/*.js` and injects each surviving single-result class's brief into its `entry[1][1][2]` scope (rendered as `span.SRScope`); per-entry fail-soft, idempotent, offline (C3). |
| `scripts/restore_definition_line.py` | fragment scan, decl-line prepend, `main(dir)` | Prepends the omitted "Definition at line N" declaration line back into inline-source fragments so they begin at their real first line; strips foreign anchors, mismatched fragments untouched; per-page fail-soft, idempotent, offline. |
| `scripts/serve_doxygen.sh` | inline flow, `PORT`, `HTML_DIR` | Standalone local preview server (`python3 -m http.server`), auto-builds docs if missing. |
| `doxygen/Doxyfile` | full config; `INPUT = src pages`, `TAGFILES`, `HTML_EXTRA_*`, `EXCLUDE_SYMBOLS` (`Ui`/`std`/`boost`/`gsl`), `BUILTIN_STL_SUPPORT=YES`, `INTERACTIVE_SVG=YES`, `OUTPUT_DIRECTORY=docs` | Base config; public API surface (`EXTRACT_PRIVATE=NO`, `INTERNAL_DOCS=NO`); `HTML_HEADER = doxygen-style-revamped/header.html` (Doxyfile:1349); `HTML_EXTRA_FILES` lists the vendored jQuery + 8 feature scripts. |
| `doxygen/Doxyfile_dev` | `@INCLUDE = doxygen/Doxyfile` + 3 overrides | Dev config: turns on private/internal extraction (`EXTRACT_PRIVATE`/`EXTRACT_PRIV_VIRTUAL`/`INTERNAL_DOCS`); inherits the base `HTML_HEADER`. This is what the script drives. |
| `doxygen-style-revamped/header.html` | `$extrastylesheet`, `$darkmode`, jQuery `<script>` first then 8 theme `<script>` tags, anti-flash inline snippet | 1.17.0 HTML head template (the single header, `HTML_HEADER` at Doxyfile:1349); loads vendored jQuery before every feature script and applies dark-mode class pre-paint. Used by both the public and dev configs. |
| `doxygen/footer.html` | `$navpath`, `$generatedby`, `$doxygenversion` | 1.17.0 footer template. |
| `doxygen/layout.xml` | `<navindex>`, custom `Docs` usergroup, `Modules` intro | Nav-tab layout (271 lines); adds a "Docs" tab group and renames some sections. |
| `doxygen/qt-tags/{qtcore,qtgui,qtwidgets}/*.tags` | Qt symbol tag DB | Enables cross-links from project symbols to `https://doc.qt.io/qt-6/`. |
| `doxygen-style-revamped/*` | `-theme.css`, `-badges.css`, `-jquery.js` (vendored jQuery 3.7.1), 8 feature `*.js`, `header.html`, `fonts/` | Vendored Qt-6-look theme (chrome + badges + jQuery-based dark-mode toggle and decoration scripts); the search-result card styling + dark search text + `#projectrow` flex + code-view legibility live in `-theme.css`. |
| `pages/index.md` | `USE_MDFILE_AS_MAINPAGE` | Doc site mainpage ("Welcome to the Qt Template documentation."). |
| `.github/workflows/doxygen.yml` | `create_docs` job, `peaceiris/actions-gh-pages@v4` | On push to `main`: build docs and force-push `docs/html` to the orphan `docs` branch. |

## Architecture & responsibilities

The pipeline is a shell orchestrator (`run_doxygen.sh`) that shells out to Doxygen and a
Python graph filter, then rewrites the generated HTML/SVG with `perl` and `find`. Nothing
is a library; everything is a process step.

```
                       make docs / CI (doxygen.yml) / serve_doxygen.sh
                                        |
                                        v
                          scripts/run_doxygen.sh  (set -euo pipefail)
   1. resolve pinned doxygen 1.17.0 ---> .doxygen-bin/1.17.0/... (fetch once, cache)
   2. require graphviz `dot`
   3. require vendored theme present
   4. fetch/verify Qt tag files -------> doxygen/qt-tags/*  (export QT_TAGS)
   5. run doxygen on Doxyfile_dev -----> reads src/ + pages/, TAGFILES=$(QT_TAGS)
        |  (@INCLUDE Doxyfile)              HTML_EXTRA_* = jquery + DSR-gated theme scripts
        |                                   EXCLUDE_SYMBOLS hides Ui/std/boost/gsl
        |  (config pipe appends a temp header + HTML_HEADER/HTML_EXTRA_FILES overrides so
        |   each DSR_* toggle adds/removes exactly its feature script; DSR_JS=0 drops all
        |   incl jQuery; the pipe restructure is in BOTH branches of the graph-filter if)
        |  if PVN_GRAPH_FILTER != 0:
        |     doxygen with DOT_CLEANUP=NO (piped) ; keep .dot next to .svg
        |     python3 filter_doxygen_graphs.py docs/html   (contract + re-render coll graphs
        |                                                    + re-sync filtered iframe dims)
        |     find docs/html -name '*.dot' -delete
        |  if search-index toggle != 0:
        |     python3 filter_search_index.py docs/html    (drop external syms + inject excerpts)
        |  if defn-restore toggle != 0:
        |     python3 restore_definition_line.py docs/html (prepend omitted decl line)
   5a. perl: force graph svg links target=_blank
   5b. perl: normalize pointer/ref spacing to east style (Type* name)
   6. copy doxygen-style-revamped/fonts/* -> docs/html/fonts/
                                        |
                                        v
                                  docs/html/  (final site)
```

Responsibility split:

- `run_doxygen.sh` owns version pinning, dependency preflight, the `DSR_*`-gated jQuery +
  theme-script emission (via the config pipe), invocation, and the `perl`/font HTML post-processing;
  it delegates graph cleanup, search filtering, and decl-line restore to the three Python scripts.
- `filter_doxygen_graphs.py` owns collaboration-graph cleanup (node contraction), SVG
  re-rendering, and the filtered-iframe dim re-sync. It is the one non-trivial algorithm in the domain.
- `filter_search_index.py` owns client-side search cleanup: drops external symbols and injects
  single-result class excerpts into `span.SRScope` (contract C3, consumed by the theme card CSS).
- `restore_definition_line.py` owns prepending the omitted declaration line into inline-source fragments.
  All three Python post-processors are pure-function + `main(dir)`, per-unit fail-soft, idempotent, offline.
- The `Doxyfile`/`Doxyfile_dev`/`header.html`/`footer.html`/`layout.xml`/theme are
  declarative inputs, not code. The 8 theme feature scripts are jQuery-based (entry `jQuery(function($){...})`),
  loaded after the vendored `-jquery.js`.
- `serve_doxygen.sh` and the `Makefile` `docs-serve` target are two independent preview
  paths (see Gotchas - they are not the same code).

## Data structures & models

### `Doxyfile` vs `Doxyfile_dev` (the `@INCLUDE` relationship)

`doxygen/Doxyfile_dev` is a 4-line delta on top of the 2780-line base:

```
@INCLUDE = doxygen/Doxyfile
EXTRACT_PRIVATE       = YES
EXTRACT_PRIV_VIRTUAL  = YES
INTERNAL_DOCS         = YES
```

The base `Doxyfile` documents the **public API only** (`EXTRACT_PRIVATE = NO`,
`INTERNAL_DOCS = NO`, `HTML_HEADER = doxygen-style-revamped/header.html` at `Doxyfile:1349`). `Doxyfile_dev`
`@INCLUDE`s it and flips the three extraction flags so private/protected/internal members
appear; it does NOT override `HTML_HEADER`, so both configs render with
`doxygen-style-revamped/header.html`. `run_doxygen.sh:20` hardcodes
`CONFIG=doxygen/Doxyfile_dev`, so the default build produces the full internal-docs site.
To publish public-only docs you point `CONFIG=` (or the `README` says the `CONFIG=` variable)
at `doxygen/Doxyfile`.

Load-bearing base settings that the pipeline depends on:

- `INPUT = src pages`, `RECURSIVE = YES`, `USE_MDFILE_AS_MAINPAGE = pages/index.md`,
  `IMAGE_PATH = pages`.
- `EXCLUDE = doxygen-style-revamped test cmake conan icon include doxygen README.md`;
  `EXCLUDE_PATTERNS = ui_* moc_*` (keeps generated Qt files out);
  `EXCLUDE_SYMBOLS = Ui std boost gsl` (`Doxyfile:1055-1063`) hides the generated/external
  namespaces from the namespace listing while `SHOW_NAMESPACES` stays `YES` and project
  `myOwnNamespace*` + class pages still render.
- `BUILTIN_STL_SUPPORT = YES` and `TAGFILES = $(QT_TAGS)/qtcore/qtcore.tags=https://doc.qt.io/qt-6/ ...`
  (three modules). These two are exactly why library nodes appear in graphs and why the
  Python filter exists.
- `HAVE_DOT = YES`, `DOT_IMAGE_FORMAT = svg`, `INTERACTIVE_SVG = YES`,
  `COLLABORATION_GRAPH = YES`, `DOT_GRAPH_MAX_NODES = 500`, `DOT_CLEANUP = YES` (base value;
  the graph-filter branch overrides it to `NO` on the fly).
- `HTML_EXTRA_STYLESHEET` = theme.css, badges.css, and the two per-font CSS files;
  `HTML_EXTRA_FILES` = the vendored `doxygen-style-revamped-jquery.js` + **eight**
  `doxygen-style-revamped-*.js` feature scripts (`run_doxygen.sh` rewrites this list per the
  `DSR_*` toggles, dropping a disabled feature's file and dropping jQuery too on `DSR_JS=0`).
- `HTML_COLORSTYLE = LIGHT` - Doxygen's own dark mode is off; the theme's own jQuery toggle
  drives dark mode via `localStorage['doxygen-darkmode']`.
- `PREDEFINED = Q_DISABLE_COPY_MOVE(x)= Q_DISABLE_COPY(x)= Q_DISABLE_MOVE(x)=` (strips the
  Qt copy/move macros so signatures render cleanly).

### `.dot` graph model (input to the filter)

Each collaboration graph is a `*.dot` file where nodes are `Node<id> [ ... URL="..." label="..." ... ];`
and edges are `Node<src> -> Node<dst> [ ... ];`. Contract the filter relies on:

- `Node1` is always the graph subject/root and is never removed (`filter_doxygen_graphs.py:139-140`).
- Edges point **content -> owner** (a member's type points at the class that owns it), so
  walking dst-ward reaches the owner (`walk_to_kept`, lines 148-160).
- A node is "library" (removable) if its `URL` resolves through a Qt tag file
  (`.tags$` or `doc.qt.io`) or contains `boost`, or if it has no URL and its label matches
  an STL name (`_STL_NAMES`/`_STL_RE`) or starts with `boost::` (`is_lib_node`, lines 98-115).

### SVG scaffold model (output re-render)

`rerender_svg` (lines 226-269) handles three Doxygen SVG shapes, each with a distinct
anchor: light-interactive (`<g id="graph0">`), zoomable (`<g id="viewport">` plus
`var viewWidth/viewHeight` and a `<!--zoomable N -->` marker), and the static "open
original" `_org.svg` (`<g id="page0,1_graph0">`). It splices graphviz's freshly laid-out
body into the original scaffold byte-for-byte so Doxygen's `svg.min.js` interactivity keeps
working.

## Control & data flow

Happy path, `bash scripts/run_doxygen.sh` (or `make docs`):

1. Resolve repo root, `cd` there; set `DOXY_VER=1.17.0`, `CONFIG=doxygen/Doxyfile_dev`,
   `TAGS_DIR=doxygen/qt-tags`, `MODULES="qtcore qtgui qtwidgets"`,
   `DOXYGEN_BIN="${DOXYGEN_BIN:-$DOXY_HOME/bin/doxygen}"` (`run_doxygen.sh:11-24`).
2. **Step 1 - pinned binary** (`:40-68`). `doxy_is_pinned()` returns true only if the
   binary exists and `--version` begins with `1.17.0`. Preference order: pre-set
   `DOXYGEN_BIN` -> a system `doxygen` that happens to be 1.17.0 -> download into
   `.doxygen-bin/1.17.0/`. Download tries `https://www.doxygen.nl/files/doxygen-1.17.0.linux.bin.tar.gz`
   then a GitHub-releases fallback, `tar -xzf`, `chmod +x`, then re-verifies the pin.
3. **Step 2 - graphviz** (`:70-74`): abort if `dot` is absent.
4. **Step 3 - theme** (`:76-81`): abort if
   `doxygen-style-revamped/doxygen-style-revamped-theme.css` is missing.
5. **Step 4 - Qt tags** (`:83-94`): for each module, if
   `doxygen/qt-tags/<m>/<m>.tags` is empty/missing, fetch it from `https://doc.qt.io/qt-6/<m>.tags`;
   a fetch failure is a **warning**, not fatal. `export QT_TAGS="$REPO_ROOT/doxygen/qt-tags"`
   - this is the variable the `Doxyfile` `TAGFILES` lines interpolate via `$(QT_TAGS)`.
6. **Step 5 - build** (`:96-` onward). The config is always piped to `doxygen -` (reads config
   from stdin) with an appended temp header + `HTML_HEADER`/`HTML_EXTRA_FILES` overrides so
   each `DSR_*` toggle adds/removes exactly its feature script (injection into the emitted
   header AND the copied `HTML_EXTRA_FILES` list); jQuery is emitted before every feature
   script iff >=1 feature is on, and `DSR_JS=0` drops all feature scripts AND jQuery. This
   pipe restructure is present in BOTH branches of the graph-filter `if`. If
   `PVN_GRAPH_FILTER != 0` (default on): also append `DOT_CLEANUP = NO` so the `.dot`
   sources survive, run `python3 filter_doxygen_graphs.py docs/html`, then
   `find docs/html -name '*.dot' -delete`. Doxygen writes to `docs/html`
   (`OUTPUT_DIRECTORY=docs`, `HTML_OUTPUT=html`).
   - Inside the graph filter (`process` loops graphs, `process_graph` handles one atomically):
     list `*__coll__graph.dot` (kind from `PVN_GRAPH_FILTER_TYPES`, default `coll`),
     `filter_dot` each (contract library nodes), re-render with `dot -Tsvg`, fix up the URL
     placeholder (`xlink:href="$` -> `xlink:href="`, add `target="_blank"`), splice into both
     `X.svg` and `X_org.svg` via `rerender_svg`, **re-sync the graph's iframe `width`/`height`
     to the shrunk SVG via `pt_to_px`=`ceil(pt*4/3)`** (on the success path, before returning
     the 3-tuple `(n, len(merges), iframes)`), rewrite the `.dot`, and delete the stale `.md5`.
     Any per-graph failure is caught (`GraphFilterError`), the original SVGs/iframe kept, and
     the loop continues.
   - **Step 5-search** (search-index toggle default on): `python3 filter_search_index.py
     docs/html` drops external (`http(s)://`) symbols from `docs/html/search/*.js` (emptied
     letter files stay valid `var searchData=[];`) and injects each surviving single-result
     class's trimmed HTML-escaped brief into its `entry[1][1][2]` scope; briefless classes
     stay empty. Per-entry fail-soft, idempotent.
   - **Step 5-defn** (defn-restore toggle default on): `python3 restore_definition_line.py
     docs/html` prepends the omitted "Definition at line N" declaration line into inline-source
     fragments (foreign anchors stripped; mismatched fragments untouched). Per-page fail-soft,
     idempotent.
7. **Step 5a** (`:110-115`): `find docs/html -maxdepth 1 -name '*graph*.svg'` and `perl`
   rewrite `target="_parent"|_top"` -> `target="_blank"` for the native (non-coll) graphs
   the filter did not touch.
8. **Step 5b** (`:117-127`): `perl` normalize pointer/reference spacing from Doxygen's west
   style (`Type *name`) to the repo's east style (`Type* name`) - but only inside specific
   declaration cells (`memItemRight`, `paramtype`, `memname`, ...) and skipping
   `*_source.html`, with a per-line class gate so operators like `return *this` in code
   blocks are untouched.
9. **Step 6** (`:129-135`): `rm -rf docs/html/fonts && mkdir -p docs/html/fonts` then copy
   `doxygen-style-revamped/fonts/*.{eot,woff2,woff,ttf,svg}` into it, because Doxygen
   flattens `HTML_EXTRA_STYLESHEET/_FILES` and never copies the `fonts/` subdir the
   `@font-face url('fonts/...')` rules reference.

Serving: `make docs-serve` (Makefile:36-37) delegates to `bash scripts/serve_doxygen.sh`,
which builds docs if `docs/html/index.html` is absent, then `exec python3 -m http.server
"$PORT" --bind 127.0.0.1 --directory "$HTML_DIR"` (`PORT` defaults to 8000). The serve logic
is single-sourced in that script.

CI: `.github/workflows/doxygen.yml` on push to `main` installs graphviz, runs
`bash scripts/run_doxygen.sh`, and deploys `./docs/html` to the orphan `docs` branch via
`peaceiris/actions-gh-pages@v4` (`force_orphan: true`).

## Public API / contracts

Other domains rely on these stable surfaces:

- **Commands / targets**: `bash scripts/run_doxygen.sh`; `make docs`; `make docs-serve`;
  `make docs-clean`; `bash scripts/serve_doxygen.sh`;
  `python3 scripts/filter_doxygen_graphs.py <html-dir> [--dot PATH]`.
- **Output contract**: the site is always produced at `docs/html/` (from
  `OUTPUT_DIRECTORY=docs` + `HTML_OUTPUT=html`), entry `docs/html/index.html`. CI's
  `publish_dir: ./docs/html` depends on this exact path.
- **Environment inputs** (the knobs):
  - `DOXYGEN_BIN` - pre-point to a 1.17.0 binary to skip download.
  - `PVN_GRAPH_FILTER` - `0` disables the collaboration-graph filter (default on).
  - `PVN_GRAPH_FILTER_TYPES` - comma list of graph kinds, default `coll` (`inherit` opt-in).
  - `DSR_*` build-time theme toggles (`PVN_GRAPH_FILTER` semantics: `0` off, else on, default
    all-on): `DSR_DARKMODE`, `DSR_BADGES`, `DSR_CODE_PUNCT`, `DSR_INHERITED`, `DSR_KEYWORDS`,
    `DSR_COLORMEMBERS`, `DSR_PERMALINK`, `DSR_RESIZE` each drop exactly their feature script
    (injection + copy); `DSR_JS=0` is the master off (drops all feature scripts AND jQuery).
    Feature->filename mapping is frozen (contract C2). A disabled feature's script is neither
    injected into HTML nor copied to output. `make docs-clean` first when checking a
    subtractive toggle - `make docs` never wipes `docs/html` and Doxygen never prunes a
    de-listed `HTML_EXTRA_FILES` entry, so a stale prior-build script false-passes.
  - the search-filter and defn-restore steps each have their own `PVN_`/`DSR_`-style env toggle
    (documented in each script header, `${VAR:-1} != "0"` semantics, default on).
  - `PORT` - `serve_doxygen.sh` listen port (default 8000).
  - `DOT` - override the `dot` binary path for the filter.
  - `QT_TAGS` - exported by `run_doxygen.sh`; consumed by `Doxyfile` `TAGFILES`
    (`$(QT_TAGS)/...`). If you invoke Doxygen without the script, you must export it.
  - `CONFIG` (script-internal at `run_doxygen.sh:20`) selects `Doxyfile` (public) vs
    `Doxyfile_dev` (internal).
- **Single source of truth**: `DOXY_VER`, `MODULES`, `CONFIG`, `TAGS_DIR` all live at the
  top of `run_doxygen.sh`.
- **Theme contract** (from `doxygen-style-revamped/README.md`): dark mode = `<html class="dark-mode">`,
  persisted in `localStorage['doxygen-darkmode']` (`'dark'`/`'light'`); palette CSS vars
  (`--pvn-accent`, `--pvn-link`, `--*-mlabel-color`, ...) are the naming contract badges and
  chrome read.
- **Filter exit code**: `process()` returns `1` ONLY when every graph failed (>=1 failure
  and zero successes/skips), else `0` (`filter_doxygen_graphs.py:380`); a single failed graph
  is warned, its original SVGs kept, and the build continues.

## Dependencies

Inbound (callers into this domain):

- `Makefile:33` `make docs` -> `bash scripts/run_doxygen.sh`; `Makefile:35-36` `docs-serve`;
  `Makefile:38-39` `docs-clean`.
- `.github/workflows/doxygen.yml:24` -> `bash scripts/run_doxygen.sh`.
- `scripts/serve_doxygen.sh:19` -> `run_doxygen.sh` (when docs missing).
- `README.md:573` documents pointing `CONFIG=` at a Doxyfile.
- `run_doxygen.sh:104` -> `filter_doxygen_graphs.py`.

Outbound (what this domain needs):

- **Doxygen 1.17.0** binary - fetched from `doxygen.nl` (primary) / GitHub releases
  (fallback).
- **graphviz `dot`** - required (`HAVE_DOT=YES`); the filter also spawns `dot -Tsvg`.
- **python3** - filter script and both HTTP preview servers.
- **`curl`, `tar`, `perl`, `find`, `xargs`** - fetch, unpack, and HTML/SVG post-processing.
- **Qt tag files** from `https://doc.qt.io/qt-6/{qtcore,qtgui,qtwidgets}.tags`.
- **Vendored theme** `doxygen-style-revamped/**` (CSS, JS, fonts) - in-tree, no network.
- **Inputs read**: `src/**` and `pages/**` (the app/library source and doc pages).

## Invariants & assumptions

- Doxygen must be exactly `1.17.0` (prefix match in `doxy_is_pinned`). The header/footer are
  1.17.0-format templates (`<!-- ... doxygen 1.17.0 -->`); a version mismatch can leave
  template variables (`$darkmode`, `$treeview`, ...) unexpanded.
- `graphviz dot` must be installed, or the build aborts at step 2.
- `QT_TAGS` must be exported before Doxygen runs (the script does this; direct invocations
  must too).
- Graph-filter assumptions: `Node1` is the graph root; collaboration-graph edges point
  content -> owner; SVGs are one of exactly three known scaffold shapes. Any of these
  breaking makes the splice return `None` (reported as a failure).
- `DOT_CLEANUP=NO` must be in effect during the filtered run so `.dot` sources survive next
  to the `.svg` files (`run_doxygen.sh:103`).
- `CREATE_SUBDIRS = NO` - steps 5a/5b use `find ... -maxdepth 1`, so all HTML/SVG must sit
  directly in `docs/html`. Flipping `CREATE_SUBDIRS` on would silently skip nested files.
- `ErrorTypeStr[]`-style manual-sync concerns do not apply here, but the `Doxyfile` is a full
  dumped config: its ~2780 lines must stay compatible with the pinned Doxygen version on any
  bump.

## Error handling & edge cases

- **No cached binary + offline**: download fails, script prints an actionable error and
  `exit 1` (`run_doxygen.sh:56-57`).
- **Missing graphviz / missing theme**: hard `exit 1` at steps 2/3.
- **Offline with no Qt tag cache**: step 4 emits `WARN: Qt tag links for <m> skipped` and
  removes the empty file; the build continues without Qt cross-links (graceful degrade).
- **`dot` fails on one graph**: raised as `GraphFilterError`, caught per-graph; the graph's
  ORIGINAL SVGs are kept, a warning naming the graph is emitted, and the loop continues.
  `process()` still returns `0` as long as at least one graph succeeded or was skipped, so one
  bad graph no longer fails the build; only an all-fail run exits `1`. Successfully rewritten
  `.dot` files are left for the driver's `find ... -delete`.
- **Scaffold splice fails** (`rerender_svg` returns `None`): raised as `GraphFilterError`;
  BOTH original SVGs of that graph are kept (the pair is rewritten atomically or not at all),
  the failure is warned, and the build continues.
- **Nothing to strip**: `filter_dot` returns `(None, 0)` and the graph is skipped untouched.
- **graphviz URL placeholder**: graphviz emits Doxygen's literal `$Class.html`; the filter
  strips the leading `$` and adds `target="_blank"` so links resolve.
- **`.md5` staleness**: after rewriting a `.dot`, the filter deletes the sibling `.md5` so
  Doxygen's next incremental run regenerates rather than skipping on an unchanged checksum.

## Concurrency / async / lifecycle

Mostly serial. `Doxyfile` sets `NUM_PROC_THREADS = 1` (single-threaded parse) and
`DOT_NUM_THREADS = 0` (graphviz auto). The filter spawns `dot -Tsvg` subprocesses one graph
at a time. The preview servers are single-threaded blocking `http.server` processes
(`serve_doxygen.sh` `exec`s and runs until Ctrl-C). CI adds a `concurrency` group with
`cancel-in-progress: true`, so a newer push cancels an in-flight docs build, and deploy uses
`force_orphan` (each publish replaces the `docs` branch history). No shared mutable state
races within a single run.

## Performance

- Collaboration graphs are effectively rendered by `dot` **twice**: once by Doxygen (with
  `DOT_CLEANUP=NO`) and again by the filter's `dot -Tsvg` re-render (`filter_doxygen_graphs.py:288`).
  Cost scales with the number of `*__coll__graph.dot` files (one subprocess each).
- `LOOKUP_CACHE_SIZE = 0` and `NUM_PROC_THREADS = 1` mean Doxygen parsing is not tuned for
  speed; fine for a small template, slow if `src/` grows large.
- `DOT_GRAPH_MAX_NODES = 500` bounds graph size. The `perl` post-passes each read/rewrite
  every `docs/html/*.html` once. All acceptable at template scale; none of it caches across
  runs beyond the pinned-binary and Qt-tag disk caches.

## Gotchas & footguns

1. **Editing the script changes what CI ships**: `run_doxygen.sh:8` now names the active CI
   counterpart (`.github/workflows/doxygen.yml`), which runs this exact script on every push
   to `main` and deploys `docs/html` to the orphan `docs` branch - so editing the script's
   post-processing changes what CI publicly ships. (The old stale `workflows/disabled/...`
   reference has been removed.)
2. **`qt-tags` is a gitignored local cache**: `run_doxygen.sh` and `CLAUDE.md` now both
   describe `doxygen/qt-tags/` as a gitignored local cache fetched on demand (`.gitignore:381`
   ignores it). On CI / a fresh clone the tags are re-fetched every run; a fresh **offline**
   clone gets no Qt cross-links (step 4 just warns).
3. **`.doxygen-bin/` and `docs/` are gitignored** (`.gitignore:379-380`): the pinned binary
   is re-downloaded on every fresh checkout/CI run, and generated docs are never tracked.
4. **One HTML header**: `header_dev.html` has been deleted and `Doxyfile_dev` no longer
   overrides `HTML_HEADER`, so both the public and dev configs render with the single
   `doxygen-style-revamped/header.html` (`HTML_HEADER` at `Doxyfile:1349` - NOT
   `doxygen/header.html`, which does not exist). Edit that one file to change either site - no
   duplicate to keep in sync. It loads the vendored `-jquery.js` before every feature script;
   the anti-flash inline snippet stays first and runs pre-jQuery.
5. **`make docs-serve` delegates to `serve_doxygen.sh`**: the Makefile target (`docs-serve:
   docs`) runs `bash scripts/serve_doxygen.sh`, which binds `127.0.0.1`, honors `PORT`
   (default 8000), and auto-builds missing docs. The serve logic is single-sourced in the
   script - no separate inline implementation remains.
6. **A single graph SVG failure no longer fails the whole build**: the filter is fail-soft
   per graph (keeps that graph's original SVGs, warns, continues) and returns nonzero only if
   EVERY graph failed; successfully rewritten `.dot` files are left for the driver's
   `find ... -delete`.
7. **The filter is author-flagged "vibe coded"** (`filter_doxygen_graphs.py:2`,
   `run_doxygen.sh:2`, `serve_doxygen.sh:2` all carry
   `WARNING: vibe coded. Works, but read with suspicion before extending.`). Its SVG splice
   is tightly coupled to Doxygen 1.17.0's exact output shape (`id="viewport"`,
   `id="graph0"`, `id="page0,1_graph0"`, the `<!--zoomable N -->` marker,
   `var viewWidth/viewHeight`). A Doxygen version bump is likely to break `rerender_svg`
   silently (returns `None` -> reported failure).
8. **Graph filter is coll-only by design**: `PVN_GRAPH_FILTER_TYPES` accepts `inherit`, but
   the node-contraction algorithm and the AssetManager example are reasoned about for
   collaboration graphs; inherit is opt-in and less exercised. New-tab link forcing for
   inheritance graphs is handled separately in step 5a's `perl`, not by the filter.
9. **Theme README is out of date**: `doxygen-style-revamped/README.md:26` says the theme is
   "wired ... as a submodule" (it is vendored in-tree, and `run_doxygen.sh` explicitly
   says "vendored, not a submodule"), its file table / load-order list only mention
   4 JS files while `HTML_EXTRA_FILES` and `header.html` now load the vendored jQuery + **8**
   feature scripts, and it still calls the scripts "vanilla, no jQuery" though all 8 have been
   ported onto jQuery (entry `jQuery(function($){...})`, loaded after `-jquery.js`). README
   refresh is known out-of-scope debt.
10. **`pages/Test.md` is leftover placeholder content** (`[Project name]`,
    `[List of features]`, `&ndash;`) that is included in `INPUT` and rendered as a real doc
    page.

### Known dead ends (from git history / comments)

- **doxygen-awesome-css was abandoned** in favor of the self-contained vendored theme:
  `doxygen-style-revamped/README.md:3-4` states it "Replaces doxygen-awesome-css", and the
  theme + 1.17.0 Doxyfiles landed together in commit `66fa21e`
  ("vendor doxygen-style-revamped theme, upgrade Doxyfiles to 1.17.0"). Do not reintroduce
  doxygen-awesome; the chrome now assumes the `--pvn-*` palette and jQuery-based feature scripts.
- **System Doxygen 1.9.x was rejected** because of a type-token bug: `void/const/int/virtual`
  cross-resolve to the global `*_cast` tag entries, so keywords render as `<a>` links and
  lose keyword coloring (`run_doxygen.sh:41-42`). That is the entire reason for the offline
  1.17.0 pin - do not "simplify" by using the system binary.
- **`BUILTIN_STL_SUPPORT` / Qt `TAGFILES` were deliberately kept on** even though they inject
  library nodes into graphs; the project chose to keep accurate signatures + Qt prose links
  and remove the noise from graphs only, via the Python filter, rather than disabling those
  settings (`filter_doxygen_graphs.py:8-9`).

## Tech debt & smells

- `scripts/filter_doxygen_graphs.py:2` - self-declared "vibe coded"; brittle regex/string
  SVG splicing pinned to one Doxygen version.
- `doxygen-style-revamped/README.md:26,34` - stale ("submodule", 4 of 8 JS files).
- `doxygen/Doxyfile` - a full 2780-line dumped config where only ~5 lines diverge in
  `Doxyfile_dev`; every Doxygen bump requires re-diffing the whole file, and drift between
  the two is easy to miss.
- `pages/Test.md` - placeholder template content shipped as a doc page.

## Test surface

**The three Python post-processors now have standalone unit tests**, but the pipeline as a
whole is still validated by running it. `scripts/test_filter_search_index.py` (16 asserts),
`scripts/test_restore_definition_line.py` (17), and `scripts/test_filter_doxygen_graphs.py`
(7) are standalone `python3`-assert suites (no pytest) run directly (`python3 scripts/test_*.py`),
NOT wired into CTest. The `test/` directory still holds only C++ Qt Test executables
(`test/gslLinkTest.cpp`, `test/integrationSmokeTest.cpp`, `test/testTest.cpp`); none reference
Doxygen, `docs/html`, or the scripts, and `cmake/` has no docs hook. The graph node-contraction
and SVG re-render remain covered only by the graph-filter suite + eyeballing.

The pipeline is validated by **running it**:

- Build (and implicitly smoke-test) the docs:
  ```bash
  bash scripts/run_doxygen.sh          # or: make docs
  ```
  Under `set -euo pipefail`, any missing dependency, Doxygen failure, or filter SVG failure
  makes this exit nonzero - which is also the CI gate (`.github/workflows/doxygen.yml` runs
  exactly this command on push to `main`; a failed build fails CI before deploy).
- Preview locally:
  ```bash
  make docs-serve                      # http.server on :8000 (all interfaces)
  PORT=9000 bash scripts/serve_doxygen.sh   # 127.0.0.1:9000, auto-builds if missing
  ```
- Filter self-check / usage:
  ```bash
  python3 scripts/filter_doxygen_graphs.py --help
  ```
- Build without the graph filter (isolate a filter regression):
  ```bash
  PVN_GRAPH_FILTER=0 bash scripts/run_doxygen.sh
  ```

Conspicuously untested: the graph node-contraction correctness (`filter_dot`/`walk_to_kept`),
the three-shape SVG re-render (`rerender_svg`), the east-pointer `perl` regex, and the
webfont copy - all validated only by eyeballing the rendered site. There are no fixtures for
the `.dot` inputs the filter parses.

## Extension points

- **Add a Qt module to cross-link**: append the module to `MODULES` in `run_doxygen.sh:22`
  **and** add a matching `$(QT_TAGS)/<m>/<m>.tags=https://doc.qt.io/qt-6/` line to
  `Doxyfile` `TAGFILES`. Both are required.
- **Public vs internal docs**: switch `CONFIG=` in `run_doxygen.sh:20` between
  `doxygen/Doxyfile` (public API) and `doxygen/Doxyfile_dev` (private/internal), per
  `README.md:573`.
- **Add a documentation page**: drop a `.md` (or source with doc comments) into `pages/`
  (it is in `INPUT`, `RECURSIVE`); `pages/index.md` is the mainpage
  (`USE_MDFILE_AS_MAINPAGE`), images go in `pages/` (`IMAGE_PATH`).
- **Add a theme asset**: a JS file goes in both `HTML_EXTRA_FILES` (Doxyfile) and a
  `<script>` tag in `header.html`; a CSS file goes in `HTML_EXTRA_STYLESHEET`; new fonts drop
  in `doxygen-style-revamped/fonts/` and are copied by step 6.
- **Graph-filter kinds**: `PVN_GRAPH_FILTER_TYPES` (env) plus the `_KIND_SUFFIX` map
  (`filter_doxygen_graphs.py:35`) - add a kind by extending the map and confirming the
  content->owner edge assumption holds for that graph type.
- **Dev-only header customization**: `Doxyfile_dev` now inherits the base
  `doxygen/header.html`. To give the internal-docs site a distinct header, re-add an
  `HTML_HEADER` override in `Doxyfile_dev` pointing at a new file.
- **Doxygen version bump**: change `DOXY_VER` in `run_doxygen.sh:17`, regenerate/`@INCLUDE`
  the `Doxyfile`, re-emit `header*.html`/`footer.html`/`layout.xml` with the new
  `doxygen -w html` templates, and re-verify `filter_doxygen_graphs.py`'s SVG scaffold
  anchors still match.
