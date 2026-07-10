# qt6-template - codebase summary

Generated: commit `54f3db7` (branch `plan-integration`, working tree dirty: `plan/**` and `.claude/skills/graphify/**` deleted, `scripts/*` comment-only edits uncommitted)

## What this is

A C++17 desktop-application template built on Qt6 (Widgets) with Boost and Microsoft GSL. It builds two targets from one source set - the executable `qt6-template` and the static library `qt6-template_LIB` that tests link against - and ships with a complete supporting scaffold: Conan dependency management, a Make convenience layer, Qt Test/CTest auto-discovery, a pinned Doxygen documentation pipeline with a vendored theme, six GitHub Actions workflows (multi-OS build, docs deploy, autotag releases), and a vendored Claude Code skill toolkit for AI-assisted plan/build/audit workflows.

## Tech stack & how to run

Languages and tools: C++17 (enforced globally), CMake >= 3.x with Ninja, Conan 2 (`boost/1.91.0`, `ms-gsl/4.2.2`), Qt 6.11 (6.8 LTS documented fallback, resolved via `find_package`, not Conan), Qt Test + CTest, Doxygen 1.17.0 (pinned, cached in `.doxygen-bin/`), Python 3 (docs graph filter), GNU Make (convenience wrapper), clang-format / clang-tidy.

Exact commands (all verified against the repo):

- Deps: `make conan` (or `bash conanLibrariesInstall.sh`) - Conan install for Debug + Release. Must run BEFORE configure; `make configure` does NOT depend on it.
- Configure: `cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release` (= `make configure`)
- Build: `cmake --build build --config Release` (= `make build`)
- Run: `make run`
- Test (all): `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -VV` (= `make test`)
- Test (one): `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -R gslLinkTest -V`
- Docs: `make docs` (= `bash scripts/run_doxygen.sh`); serve: `make docs-serve` (localhost:8000); clean: `make docs-clean`
- Format: `make format` (clang-format in place)
- Lint: `make tidy` (clang-tidy; needs a configured build). CI-workflow lint: actionlint (not installed locally; see `summary/05-ci.md` for the download one-liner)
- Typecheck: none separate (compiler is the typechecker)

Sanitizer/coverage knobs at configure time (`cmake/StandardSettings.cmake`, prefix `qt6-template_`): `ENABLE_ASAN`, `ENABLE_UBSAN`, `ENABLE_COVERAGE` (all OFF), `ENABLE_LTO` (ON), `WARNINGS_AS_ERRORS` (OFF). Flags are directory-scoped, so they reach the test binaries too.

Git policy (from the vendored skill chain): plan work happens on branch `plan-integration` (fork base and merge target, never pushed/pulled to origin); features build in `feat/NN-<slug>` worktrees with `task/` sub-worktrees; local merges allowed. `main` is the PR target.

**Available tooling (discovered, not assumed):** MCP servers: token-savior (symbol-level find/read/edit, deferred tools via ToolSearch), context7 (library docs). NOT present despite CLAUDE.md references: graphify graph (`graphify-out/graph.json` does not exist; the `/graphify` skill is deleted in the working tree), cavemem MCP (tools not loadable). CLI: cmake, ninja, conan, ctest, make, python3, clang-format, clang-tidy, git, gh. Doxygen 1.17.0 auto-downloaded to `.doxygen-bin/` by `scripts/run_doxygen.sh`. actionlint NOT on PATH. Vendored Claude Code skills under `.claude/skills/` (22 on disk; see AI-tooling domain).

## Validation gate ladder

1. Gate 1 build: `cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release && cmake --build build --config Release`
2. Gate 2 unit: `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -VV` (4 tests: `testTest`, `gslLinkTest`, `integrationSmokeTest`, `errorHandlingTest`; verified 4/4 pass on Qt 6.11.1)
3. Gate 3 integration: `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -R integrationSmokeTest -V` (Qt + Boost>=1.91 + ms-gsl together)
4. Gate 4 perf/bench: none
5. Gate 5 smoke/launch: `QT_QPA_PLATFORM=offscreen ./build/qt6-template --self-test` (constructs + shows MainWindow, quits through one event-loop pass, exits 0 within 15s, offscreen-safe); `make run` is the interactive equivalent. Docs smoke: `bash scripts/run_doxygen.sh` exits nonzero on failure and must produce `docs/html/index.html`.
6. Gate 6 human/GUI review: `make run` (needs a display); docs review: `make docs-serve` -> http://localhost:8000

## Domain map

| # | Domain | Report | One-liner | Owned paths (globs) | Key contracts exposed |
|---|--------|--------|-----------|---------------------|----------------------|
| 01 | Build system & deps | [01-build-system.md](01-build-system.md) | CMake two-target build, Conan deps, Make wrapper, lint configs | `CMakeLists.txt`, `CMakePresets.json`, `cmake/**`, `conan/conanfile.txt`, `Makefile`, `conanLibrariesInstall.{sh,ps1}`, `requirements.txt`, `.clang-format`, `.clang-tidy`, `config.desktop`, `icon/**` | targets `qt6-template` / `qt6-template_LIB`, option set `qt6-template_*`, vars `SOURCE_FILES`/`TEST_FILES`/`MODULES`, presets `ninja-release`/`ninja-debug`, 12 Make targets |
| 02 | App core | [02-app-core.md](02-app-core.md) | Qt Widgets app: main(), MainWindow, exception/message-handler funnel | `src/**` | `AppException`, `enum class ErrorType` (XXZZ), `errorMessageHandler`, `operator<<(QDebug,ErrorType)`, `ERROR_MESSAGE` macro |
| 03 | Testing | [03-testing.md](03-testing.md) | QTEST_MAIN-per-.cpp auto-discovered CTest suite linking the static lib | `test/**` (plus `TEST_FILES` glob lines in `cmake/Sources.cmake:6-7` - file owned by 01) | drop-a-`.cpp` auto-discovery, `<name>_Tests` targets, link-`qt6-template_LIB` rule, offscreen-QPA rule |
| 04 | Docs pipeline | [04-docs-pipeline.md](04-docs-pipeline.md) | Pinned Doxygen 1.17.0 + vendored theme + graph-filter post-processing | `doxygen/**`, `scripts/**`, `doxygen-style-revamped/**`, `pages/**`, `.doxygen-bin/**` (gitignored), `docs/**` (gitignored) | `bash scripts/run_doxygen.sh`, `make docs*`, output `docs/html/index.html`, env `DOXYGEN_BIN`/`PVN_GRAPH_FILTER`/`PORT` |
| 05 | CI/CD | [05-ci.md](05-ci.md) | 6 GitHub Actions workflows: multi-OS build/test, docs deploy, autotag releases | `.github/workflows/**`, `.github/dependabot.yml` | workflow name `Autotag` (workflow_run trigger key), release artifacts (AppImage / macOS tar.gz / Win zip), orphan `docs` branch, `X.Y.Z` patch-only tags |
| 06 | AI tooling | [06-ai-tooling.md](06-ai-tooling.md) | Vendored Claude Code skill chain (capture -> plan -> build -> audit) | `.claude/skills/**`, `.claude/settings.local.json` (slices of `CLAUDE.md`, `README.md`, `.gitignore` shared) | branch `plan-integration`, `feat/NN-<slug>` naming, id grammar `R*`/`AC*.*`/`C*`, verdicts `SHIP|REVISE|BLOCK`, artifact files `plan/*.md`, `summary/overview.md` |

Overlaps flagged: `cmake/Sources.cmake` (01 owns the file, 03 owns the `TEST_FILES` glob lines); `Makefile` docs targets (01 owns the file, 04 owns docs behavior); `.github/workflows/doxygen.yml` (05 owns the workflow, 04 owns the script it runs); `CLAUDE.md`/`README.md` sections split between 01/04/06.

## Cross-domain contract candidates

Boundaries any multi-domain change must freeze:

1. **Target pair `qt6-template` + `qt6-template_LIB`** (built at `CMakeLists.txt:86-116`). The static lib is the test-linkage surface (`test/CMakeLists.txt:69-75` selects `qt6-template_LIB` when `${PROJECT_NAME}_BUILD_EXECUTABLE=ON`). Domains: build-system <-> testing <-> app-core.
2. **Test auto-discovery glob**: `cmake/Sources.cmake:6-7` globs `test/*.cpp`; `test/CMakeLists.txt:17-79` turns each into `<basename>_Tests` + `add_test(NAME <basename>)`. Adding a test = adding a file, never editing CMake. Domains: testing <-> build-system <-> app-core.
3. **Exception surface** (`src/Exceptions/Exceptions.h`): `AppException(const char* msg, ErrorType = General)` with public `const ErrorType errorType` and `what/raise/clone` overrides; `enum class ErrorType` in XXZZ decimal format; string mapping is a `switch` in `operator<<(QDebug, const ErrorType&)` at `Exceptions.cpp:27` - NOT the `ErrorTypeStr[]` array CLAUDE.md claims. Domains: app-core <-> testing (tests may throw/catch) <-> docs (documented API).
4. **Headless test env**: `QT_QPA_PLATFORM=offscreen` required by every test invocation - Makefile, CI, and any agent gate must set it. Domains: testing <-> build-system <-> CI.
5. **Makefile 12-target set** (frozen per CLAUDE.md): `help conan configure build run test docs docs-serve docs-clean format tidy clean`. CI and skills reference these. Domains: build-system <-> CI <-> docs <-> AI-tooling.
6. **Docs entrypoint**: `bash scripts/run_doxygen.sh` produces `docs/html/index.html`; `.github/workflows/doxygen.yml` runs exactly this and deploys `docs/html` to the orphan `docs` branch via `peaceiris/actions-gh-pages@v4`. Domains: docs <-> CI.
7. **Workflow name `Autotag`**: `ubuntu.yml`/`macos.yml`/`windows.yml` trigger deploy mode via `workflow_run.workflows: [Autotag]` - renaming `autotag.yml`'s `name:` silently breaks all releases. Domain: CI internal but rename-sensitive.
8. **Conan toolchain path**: `conan/conan_toolchain.cmake` is the configure-time contract between Conan output and CMake; gitignored and machine-local (absolute paths baked in). Domains: build-system <-> CI (CI regenerates it per job).
9. **Skill-chain grammar** (AI-tooling): branch `plan-integration`, worktrees `feat/NN-<slug>`, ids `R*`/`AC*.*`/`C*`/`FC<NN>.*`, verdicts `SHIP|REVISE|BLOCK` (plan) / `SHIP|FIX|BLOCK` (impl), artifacts `plan/orchestrator.md`, `plan/review.md`, `summary/overview.md`. Domains: AI-tooling <-> everything it plans over.

## Architecture at a glance

```
                       +---------------------+
   conanfile.txt ----> |  Conan 2            | --> conan/conan_toolchain.cmake
   (boost, ms-gsl)     +---------------------+            |
                                                          v
   Qt6 (system/aqt) -----------------------> +---------------------------+
                                             | CMake (CMakeLists.txt     |
   cmake/Sources.cmake (globs src/, test/) ->|  + cmake/*.cmake)         |
   cmake/StandardSettings.cmake (options) -> +---------------------------+
                                                |            |         |
                                v---------------+            v         v
                        qt6-template (exe)     qt6-template_LIB   <name>_Tests x3
                        [src/** : main.cpp,     (same sources,     (test/*.cpp, link
                         MainWindow,             static)            _LIB, CTest,
                         Exceptions)                |               offscreen QPA)
                                                    +----------------^
   Makefile (12 targets) -- wraps all of the above locally
   scripts/run_doxygen.sh -- Doxygen 1.17.0 + doxygen-style-revamped theme
        reads src/ + pages/ -> docs/html
   .github/workflows/ -- ubuntu|ubuntu-debug|macos|windows (build+test),
        doxygen (docs -> orphan docs branch), autotag (X.Y.Z -> triggers deploys)
   .claude/skills/ -- plan/build/audit prompt chain operating on all of it
```

## End-to-end flows that cross domains

1. **Code change -> release**: edit `src/**` (app-core) -> `cmake/Sources.cmake` glob picks it up, both targets rebuild (build-system) -> `make test` runs 4 CTest suites against `qt6-template_LIB` offscreen (testing) -> PR to `main`; on merge, `autotag.yml` pushes the next `X.Y.Z` tag -> `workflow_run` fires ubuntu/macos/windows deploy jobs -> draft prereleases with AppImage / tar.gz / zip artifacts (CI).
2. **Doc comment -> published docs**: `/// \brief` in `src/mainwindow.h` (app-core) -> `bash scripts/run_doxygen.sh` pins Doxygen 1.17.0, fetches Qt tag files, renders with the vendored theme, `filter_doxygen_graphs.py` contracts std/Boost/Qt nodes out of collaboration graphs, webfonts copied to `docs/html/fonts/` (docs) -> push to `main` triggers `doxygen.yml` which rebuilds and deploys `docs/html` to the orphan `docs` branch (CI).
3. **New test end to end**: drop `test/fooTest.cpp` containing `QTEST_MAIN` + `#include "fooTest.moc"` (testing) -> `cmake/Sources.cmake:6-7` glob + `test/CMakeLists.txt:17-79` create `fooTest_Tests` and register CTest name `fooTest` (build-system) -> runs locally via `make test` and in all four build workflows with `QT_QPA_PLATFORM=offscreen` (CI). No CMake edits.
4. **AI-assisted feature**: `/sketch` captures requirements into `NextThingsToDo.md` -> `/parallel-plan` writes `plan/` on branch `plan-integration` grounded in this `summary/` -> `/execute-plan` builds in `feat/NN-<slug>` worktrees, gating each task on the ladder above -> `/review-implementation` audits and, on SHIP, retires `plan/` (AI-tooling touching every other domain).

## Cross-cutting concerns

- **Error handling**: single funnel. `qInstallMessageHandler(errorMessageHandler)` (`src/Exceptions/Exceptions.cpp:41`) formats `[category][file:line][function]`; Info/Warning -> QMessageBox; Critical/Fatal -> `throw AppException` through the event loop; `main()` catches in a 4-tier ladder (`AppException` -> `QException` -> `std::exception` -> `...`), each catch logs to stderr, shows `QMessageBox::critical`, then returns `EXIT_FAILURE` (hardened this cycle - catches no longer rethrow; the bootstrap try/catch also returns `EXIT_FAILURE`). Known limit: stream-style `qCritical() << ...` still aborts inside `~QDebug()` (noexcept in Qt 6.11) before reaching the ladder - only directly-thrown exceptions and direct `errorMessageHandler(...)` calls exercise the clean-exit path.
- **Debug gating**: the `_DEBUG` macro (defined for Debug builds on all platforms, not just MSVC) gates stderr logging; Release silently drops Debug-level messages.
- **Config**: no runtime config system; build-time options only (`cmake/StandardSettings.cmake`, prefix `qt6-template_`). Env vars matter to tooling, not the app: `QT_QPA_PLATFORM`, `DOXYGEN_BIN`, `PVN_GRAPH_FILTER`, `PORT`.
- **Secrets**: none in-repo; CI uses the default `GITHUB_TOKEN` with least-privilege `permissions` blocks per workflow (hardened in FC04.1).
- **Logging**: `qDebug`/`qWarning`/`qCritical` through the message handler; no logging framework.
- **i18n / state / auth**: none - template scope.

## Conventions

- **C++**: C++17 (`CMAKE_CXX_STANDARD 17` enforced, no extensions). Qt style: `Q_OBJECT` in headers, AUTOMOC/AUTOUIC/AUTORCC handle codegen; `.ui` files live in `src/` and generate `ui_*.h`; QML under `src/qml/` (currently dead code behind a commented-out main).
- **Formatting**: `.clang-format` at repo root is authoritative; run `make format`. Lint with `make tidy` (`.clang-tidy`, needs configured build).
- **Doxygen comments**: `/// \brief` and `/// \param` style (reference: `src/mainwindow.h`).
- **Error idiom**: throw `AppException(msg, ErrorType::X)`; extend `enum class ErrorType` AND add a matching `case` to `operator<<(QDebug, const ErrorType&)` in `Exceptions.cpp` (NOT an `ErrorTypeStr[]` array - that is documentation drift). XXZZ values are decimal: never write a leading-zero literal like `0108` (octal, fails to compile).
- **Tests**: one `.cpp` = one Qt Test class + `QTEST_MAIN` + `#include "<basename>.moc"` in `test/`; discovery is automatic; never edit CMake to add a test; always run offscreen.
- **CMake options**: prefix new options `qt6-template_` (i.e. `${PROJECT_NAME}_`), define them in `cmake/StandardSettings.cmake`; dependency lists belong in `cmake/Modules.cmake` (`QT_COMPONENTS`, `BOOST_COMPONENTS`).
- **Makefile**: target set is frozen at 12; do not add targets casually.
- **README.md and commit messages**: ASCII punctuation only - hyphen not em-dash, `->` not Unicode arrow, no emojis.
- **Git**: plan work on `plan-integration` (local only), features in `feat/NN-<slug>` worktrees, PRs target `main`. `main` pushes trigger autotag + releases + docs deploy - merging to main IS releasing.

## Glossary

- **`qt6-template_LIB`**: static library built from the same sources as the executable; the linkage surface for tests.
- **XXZZ format**: `ErrorType` numbering scheme - XX = category, ZZ = subcategory, as decimal integers (e.g. `SomethingWrongWithArguments = 101`).
- **`_DEBUG`**: cross-platform debug macro (defined by this project's CMake for Debug builds everywhere, unlike the MSVC-only convention) gating debug logging.
- **offscreen QPA**: `QT_QPA_PLATFORM=offscreen`, the headless Qt platform plugin every test invocation needs.
- **`Doxyfile` vs `Doxyfile_dev`**: base public-API config vs the dev config that `@INCLUDE`s it and adds `EXTRACT_PRIVATE`/`INTERNAL_DOCS`; the script drives `Doxyfile_dev`.
- **graph filter**: `scripts/filter_doxygen_graphs.py` - contracts std/Boost/Qt nodes out of Doxygen collaboration graphs and re-renders the SVGs in place; toggle with `PVN_GRAPH_FILTER=0`.
- **Autotag**: `autotag.yml` workflow that pushes an auto-incremented `X.Y.Z` tag on every `main` push; its `name:` is the trigger key for the three deploy workflows.
- **plan-integration**: local-only git branch where the vendored skill chain plans and integrates features before PR to `main`.
- **`-opus` skills**: byte-for-byte duplicates of each workflow skill pinned to `claude-opus-4-8` instead of `claude-fable-5`; hand-cloned, no sync mechanism.
- **worktree-per-feature**: `/execute-plan` builds each feature in a `feat/NN-<slug>` git worktree, merging back into `plan-integration`.

## Risks, debt & open questions

Prioritized; each is something a plan must address or consciously scope out. Full detail in the per-domain reports.

1. **Phantom `ErrorTypeStr[]` documentation drift** (`CLAUDE.md:67`, `.github/copilot-instructions.md:35`): the array does not exist; the real string map is the `switch` in `operator<<(QDebug, ErrorType)` at `src/Exceptions/Exceptions.cpp:27`. Newcomers and AI agents will edit the wrong place. Fix the docs or introduce the array.
2. **Exception-through-the-event-loop design** (`Exceptions.cpp:41`): `errorMessageHandler` throws `AppException` on Critical/Fatal across `app->exec()` - Qt-version-fragile, preempts `qFatal`'s abort, and every `main()` catch rethrows so the process always dies via `std::terminate` rather than a clean exit code.
3. **Warnings only on the executable** (`CMakeLists.txt:128`): `set_project_warnings` is not applied to `qt6-template_LIB` or tests, so a warning-clean build of the exe can hide warnings in the identical sources compiled into the lib.
4. **Conan machine-locality**: `conan/` is gitignored except `conanfile.txt`; the generated toolchain bakes in absolute `/home/kyenero/.conan2/...` paths and `conan/CMakePresets.json` hard-codes binaryDir and `jobs: 24`. Fresh machines must `make conan` first, and `make configure` does not enforce that ordering.
5. **CI/local configure drift** (`.github/workflows/{ubuntu,macos,windows}.yml`): Release CI jobs omit `-G Ninja` and `-DCMAKE_BUILD_TYPE` (the `env: CMAKE_BUILD_TYPE` is never consumed by CMake at configure) and build `--target install`, while `make` uses Ninja + explicit type + default target. Same tests, different build path.
6. **Docs pipeline fragility**: `filter_doxygen_graphs.py` splices SVG against Doxygen-1.17.0-specific output (breaks on version bump; self-flagged "vibe coded"); one failed graph aborts the whole docs build under `set -e`. Stale facts: `run_doxygen.sh:8` cites a nonexistent `workflows/disabled/doxygen.yml`, and `doxygen/qt-tags` is called a "committed cache" but is gitignored (`.gitignore:381`), so CI refetches every run and offline fresh clones lose Qt cross-links.
7. **graphify skill drift**: `.claude/skills/graphify/**` deleted in the working tree but `README.md:139,186` and `CLAUDE.md:84` still advertise it ("23 skills"); `graphify-out/graph.json` does not exist. Dangling references.
8. **Dirty `plan-integration` branch**: `plan/**` retirement and `scripts/*` comment-only edits are uncommitted; the skill chain's stale-plan guard and clean-tree pre-flights will reject until committed.
9. **Duplicated link recipes** (`test/CMakeLists.txt:54-67` vs root `CMakeLists.txt:156-183`): a dependency added to the app but not the test recipe silently never reaches test binaries.
10. **Test-name regex fragility** (`test/CMakeLists.txt:18`): `[a-zA-Z0-9_ ]+` silently mangles targets for filenames containing `-` or `.`.
11. **Workflow duplication, no CI lint**: three near-identical deploy workflows must be edited in lockstep; nothing lints workflow YAML in CI (actionlint was a one-time gate); renaming the `Autotag` workflow name silently breaks all releases.
12. **Dead code in app-core**: commented-out QML `main` (`src/main.cpp:77-136`) with a latent argument-order bug at `Exceptions.cpp:82`, plus Doxygen-demo filler symbols in `mainwindow.h` - decide to resurrect or delete.
13. **`-opus` skill duplication**: 20 hand-cloned skill variants with no sync mechanism or lint; edits to one family member silently diverge from its twin.
14. **No smoke gate for the app binary**: nothing launches `qt6-template` in CI; Gate 5 is manual.
