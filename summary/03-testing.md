# Testing infrastructure — analysis

## Purpose
This subsystem gives the Qt6 template an automated, headless-capable unit-test harness built on the Qt Test framework and driven by CTest. It solves the "prove the code compiles, links against every dependency stack, and behaves" problem with a deliberately zero-ceremony convention: each `.cpp` file dropped into `test/` becomes one standalone test executable, auto-discovered by a CMake glob and registered with CTest, with no edits to any build file required. The existing tests are link/smoke tests that prove the app's static library plus Qt, Boost.filesystem, and ms-gsl all coexist and link into a test binary.

## Owned paths
This domain owns:

- `test/**` in full — `test/CMakeLists.txt`, `test/testTest.cpp`, `test/gslLinkTest.cpp`, `test/integrationSmokeTest.cpp`.

Shared / overlapping path (FLAGGED):

- `cmake/Sources.cmake` — **shared with the build-system domain.** Lines 1-4 glob `SOURCE_FILES` (the app/library sources, owned by build-system); lines 6-7 glob `TEST_FILES` (`test/*.cpp`, the test-discovery half this domain depends on). The testing domain owns only the `TEST_FILES` glob semantics; it does not own the file. Any change to this file must be coordinated with the build-system domain.

Consumed-but-not-owned (read-only inputs from the build-system domain): `cmake/Modules.cmake` (`MODULES`, `QT_COMPONENTS`, `BOOST_COMPONENTS`), `cmake/Resources.cmake` (`QML_FILES`, `TEST_RESOURCES`), `cmake/StandardSettings.cmake` (the `${PROJECT_NAME}_BUILD_EXECUTABLE` option), and the root `CMakeLists.txt` (target creation of `qt6-template_LIB`, `enable_testing`, `add_subdirectory(test)`).

## Key files & symbols
| File | Central symbol(s) | One line |
|------|-------------------|----------|
| `test/CMakeLists.txt` | `foreach(file ${TEST_FILES})` loop (`:19`), `qt_add_executable(${test_target}_Tests ...)` (`:24`), `add_test(NAME ${test_name} COMMAND ...)` (`:67-68`) | Per-`.cpp` target factory: one test source -> one `_Tests` executable -> one CTest entry. |
| `cmake/Sources.cmake` | `file(GLOB_RECURSE TEST_FILES test/*.cpp)` (`:6-7`) | The test-discovery glob; the sole input the loop above iterates. |
| `test/testTest.cpp` | `class TestQString : QObject`, slot `toUpper()`, `QTEST_MAIN(TestQString)` (`:23`) | Exercises the app library (`MainWindow`) + Qt `QString` + Boost.filesystem link. |
| `test/gslLinkTest.cpp` | `class GslLinkTest : QObject`, slot `notNullHoldsPointer()`, `QTEST_MAIN(GslLinkTest)` (`:17`) | Proves `Microsoft.GSL::GSL` (`gsl::not_null`) links into a test target. |
| `test/integrationSmokeTest.cpp` | `class IntegrationSmokeTest : QObject`, slot `qtBoostGslLinkTogether()`, `QTEST_MAIN(...)` (`:22`) | Cross-cutting proof Qt + Boost (>= 1.91.0) + ms-gsl coexist and link together. |
| root `CMakeLists.txt` | `qt_add_library(${PROJECT_NAME}_LIB STATIC ...)` (`:106`), `enable_testing(true)` (`:310`), `add_subdirectory(test)` (`:311`) | Creates the static library tests link against and wires the test subdir in. |

## Architecture & responsibilities
The harness has three cooperating layers, each with a single responsibility:

1. **Discovery** — `cmake/Sources.cmake:6-7` recursively globs `test/*.cpp` into the `TEST_FILES` CMake list. No manual registration; the file list is the test list.
2. **Target generation** — `test/CMakeLists.txt:19-69` loops over `TEST_FILES`. For each source it derives `test_name` via `get_filename_component(... NAME_WLE)` and sanitizes it to `test_target` via `string(MAKE_C_IDENTIFIER ...)` (`:20-21`), builds a Qt executable `${test_target}_Tests` (`:24`), applies `set_project_warnings` (`:25`), wires include dirs, links Qt Test + the shared dependency helper + the app static library, and calls `add_test` (`:67-68`).
3. **Execution** — CTest reads the generated `build/test/CTestTestfile.cmake`, launches each `_Tests` binary as a separate process; the binary's `QTEST_MAIN`-generated `main()` spins up a `QApplication`, runs every private slot as a test case via `QTest::qExec`, and returns the failure count as its exit code.

```
cmake/Sources.cmake                 test/CMakeLists.txt                 CTest / runtime
  file(GLOB TEST_FILES              foreach(file IN TEST_FILES)          ctest -C <cfg>
       test/*.cpp) --------------->   test_name = basename(file)  ---->   reads build/test/
  [gslLinkTest.cpp,                   qt_add_executable(                    CTestTestfile.cmake
   integrationSmokeTest.cpp,            <name>_Tests file)                 for each add_test:
   testTest.cpp]                       link Qt6::Test + MODULES +           run <name>_Tests
                                        QT_COMPONENTS + Boost +              -> QTEST_MAIN main()
                                        Microsoft.GSL::GSL +                 -> QApplication
                                        qt6-template_LIB   <-- app code      -> QTest::qExec(obj)
                                       add_test(NAME test_name              -> exit(failCount)
                                                COMMAND <name>_Tests)
```

Responsibility boundary: the loop reuses the shared `project_link_dependencies` helper (the same single link recipe the app uses, defined at the end of `cmake/Modules.cmake`), then adds `Qt6::Test` and the app static library on top - so a test binary mirrors the app's link environment without a duplicated per-component recipe.

## Data structures & models
The "models" here are CMake list/option variables, not runtime types.

- `TEST_FILES` (list of absolute paths) — `cmake/Sources.cmake:6-7`. The set of test sources. Currently `{errorHandlingTest.cpp, gslLinkTest.cpp, integrationSmokeTest.cpp, testTest.cpp}`.
- `test_name` / `test_target` (strings) — `test/CMakeLists.txt:20-21`. `test_name` = `get_filename_component(${file} NAME_WLE)` (strips only the LAST extension, so dotted basenames survive); `test_target` = `string(MAKE_C_IDENTIFIER "${test_name}" ...)` (sanitizes `-`/`.` to `_`). `test_name` is the CTest test name (original basename); `test_target` with a `_Tests` suffix is the executable target name.
- `MODULES`, `QT_COMPONENTS`, `BOOST_COMPONENTS` — `cmake/Modules.cmake:3,7,5`. `MODULES` is empty; `QT_COMPONENTS = Core Gui Widgets`; `BOOST_COMPONENTS = filesystem`. Each is looped by the shared `project_link_dependencies` helper called for every test (`test/CMakeLists.txt:57`).
- `${CMAKE_PROJECT_NAME}_TEST_LIB` (string) — `test/CMakeLists.txt:59-63`. Resolves to `qt6-template_LIB` when `qt6-template_BUILD_EXECUTABLE` is ON (the default), else to `qt6-template` (used when the whole project is built as a library). Linked at `:65`.
- `QML_FILES`, `TEST_RESOURCES` — `cmake/Resources.cmake`. `TEST_RESOURCES` is `RESOURCES` with `"../"` prepended (`:16-19`), consumed only inside the QML branch or the `qt_add_resources` else-branch (`test/CMakeLists.txt:33-45`).
- `${PROJECT_NAME}_QT_QUICK` (bool) — set in root `CMakeLists.txt:42-44` if a `Quick` component is requested. Currently OFF (no `Quick` in `QT_COMPONENTS`), so the `else()` resource branch runs for tests.

The only runtime types are the four test fixtures, each a `QObject` subclass with a `Q_OBJECT` macro and one or more `private slots` that Qt Test treats as test cases.

## Control & data flow
Configure-time (CMake):

1. Root `CMakeLists.txt:83` `include(cmake/Sources.cmake)` populates `TEST_FILES`.
2. Root `CMakeLists.txt:106` creates `qt6-template_LIB` (static, same `SOURCE_FILES` as the app).
3. Root `CMakeLists.txt:310-311` calls `enable_testing(true)` then `add_subdirectory(test)`.
4. `test/CMakeLists.txt:3` finds `Qt6::Test`; `:19` iterates `TEST_FILES`.
5. Per file: `:20-21` derive `test_name` (`NAME_WLE`) and `test_target` (`MAKE_C_IDENTIFIER`); `:24` `qt_add_executable(${test_target}_Tests ${file})`; `:25` `set_project_warnings(${test_target}_Tests)`; `:27-34` add include dirs for `src/` and `src/qml`; `:55` links `Qt6::Test`; `:57` `project_link_dependencies(${test_target}_Tests)` links `MODULES`, `Qt6::Core/Gui/Widgets`, `Boost::filesystem`, `Microsoft.GSL::GSL`; `:59-65` link the app static library; `:67-68` `add_test(NAME ${test_name} COMMAND ${test_target}_Tests)`.
6. AUTOMOC (inherited from root `CMakeLists.txt:50`, set before `add_subdirectory(test)`) sees `Q_OBJECT` in each `.cpp` and generates the `<basename>.moc` that the source `#include`s at its bottom.

Build-time: each `_Tests` target compiles its one `.cpp` + generated moc and links the whole app static library plus Qt/Boost/GSL.

Run-time (per test process, happy path):

1. `QTEST_MAIN(Fixture)` expands to a `main()` that constructs a `QApplication` (a `QApplication`, not `QCoreApplication`, because `Qt6::Widgets` is linked), then `QTest::qExec(&fixture, argc, argv)`.
2. `QApplication` construction loads a QPA platform plugin; with `QT_QPA_PLATFORM=offscreen` it loads the offscreen plugin and needs no display.
3. `qExec` runs `initTestCase()`, then each `private slot` in declaration order, then `cleanupTestCase()`. (Verified: `gslLinkTest` reports "3 passed" = `initTestCase` + `notNullHoldsPointer` + `cleanupTestCase`.)
4. Each `QCOMPARE` / `QVERIFY` that fails increments the failure count and logs `FAIL!`; `main()` returns that count. CTest interprets a non-zero exit as a failed test.

Per-test assertions (what each actually checks):

- `test/testTest.cpp` `TestQString::toUpper` (`:14-21`): default-constructs a `boost::filesystem::recursive_directory_iterator it;` (link-forcing, never iterated), `new MainWindow(nullptr)` (constructs the app's real widget from the static library), asserts `QCOMPARE(str.toUpper(), QString("HELLO"))` for `str = "Hello"`, then `delete mainwindow`. It is really a link + widget-construction smoke test of the app library + Qt string + Boost.filesystem.
- `test/gslLinkTest.cpp` `GslLinkTest::notNullHoldsPointer` (`:9-14`): builds `gsl::not_null<int*> ptr(&value)` over a local `int value = 42` and asserts `QCOMPARE(*ptr, 42)`. Proves ms-gsl compiles and links.
- `test/integrationSmokeTest.cpp` `IntegrationSmokeTest::qtBoostGslLinkTogether` (`:11-19`): `QVERIFY(!QStringLiteral("template").isEmpty())` (Qt), `QVERIFY(BOOST_VERSION >= 109100)` (Boost header links and the version is >= 1.91.0), `gsl::not_null<int*> p(&v)` with `QCOMPARE(*p, 7)` (ms-gsl). Cross-cutting three-stack link proof.

## Public API / contracts
What this domain exposes and guarantees to other domains:

- **The "drop a `.cpp`" contract.** Any file matching `test/*.cpp` that defines exactly one `QTEST_MAIN(X)` and (if it declares `Q_OBJECT`) `#include`s `"<basename>.moc"` at its bottom is automatically compiled to `<basename>_Tests` and registered as CTest test `<basename>`, with no CMake edit. This is the primary contract downstream features and CI rely on (see `plan/ZZ-tests/feature.md`: "Do NOT touch `test/CMakeLists.txt` ... the glob auto-discovers the new `.cpp`").
- **CTest test names** (stable identifiers other domains and CI filter on with `ctest -R`): `testTest`, `gslLinkTest`, `integrationSmokeTest`, `errorHandlingTest`.
- **Executable target names**: `testTest_Tests`, `gslLinkTest_Tests`, `integrationSmokeTest_Tests`, `errorHandlingTest_Tests`, emitted to `build/test/`.
- **Headless contract**: the suite passes with `QT_QPA_PLATFORM=offscreen` and requires no display server. CI (`.github/workflows/ubuntu.yml:89-92`, `ubuntu-debug.yml`, `macos.yml`, `windows.yml`) and the `Makefile` `test` target depend on this.
- **Link contract**: tests link `qt6-template_LIB` (the static library), never the executable — so any symbol reachable from the app is testable. Depends on build-system keeping `qt6-template_BUILD_EXECUTABLE=ON` (default) so `_LIB` exists.

## Dependencies
Inbound (real callers into this domain):

- root `CMakeLists.txt:310-311` — `enable_testing(true)` + `add_subdirectory(test)`.
- `.github/workflows/ubuntu.yml:89-92` — `cd build/ && QT_QPA_PLATFORM=offscreen ctest -C Release -VV`.
- `.github/workflows/ubuntu-debug.yml`, `macos.yml`, `windows.yml` — the same `ctest` invocation per OS/config.
- `Makefile` `test` target — `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -VV`.

Outbound (what this domain depends on):

- Build-system domain: `cmake/Sources.cmake` (`TEST_FILES`), `cmake/Modules.cmake` (`MODULES`, `QT_COMPONENTS`, `BOOST_COMPONENTS`), `cmake/Resources.cmake` (`QML_FILES`, `TEST_RESOURCES`), `cmake/StandardSettings.cmake` (`_BUILD_EXECUTABLE`), and the `qt6-template_LIB` target from root `CMakeLists.txt:106`.
- Libraries: `Qt6::Test`, `Qt6::Core`, `Qt6::Gui`, `Qt6::Widgets`, `Boost::filesystem` (`boost/1.91.0`), `Microsoft.GSL::GSL` (`ms-gsl/4.2.2`), plus the app static library.
- App source: `src/mainwindow.h` / `MainWindow` (via `testTest.cpp:2`), linked from `qt6-template_LIB`.
- Toolchain: Conan-provided Boost/ms-gsl, `find_package(Qt6 ...)` for Qt, CMake AUTOMOC.

## Invariants & assumptions
- **One `QTEST_MAIN` per file.** Two in one `.cpp` -> two `main()` -> link error. One `.cpp` = one executable = one `add_test`.
- **`.moc` include name must equal the basename.** `test/testTest.cpp:24` `#include "testTest.moc"`; a mismatch fails AUTOMOC/compile.
- **Filenames with `-` or `.` produce valid targets.** `get_filename_component(... NAME_WLE)` strips only the last extension (dotted basenames survive) and `string(MAKE_C_IDENTIFIER ...)` sanitizes the target name (`test/CMakeLists.txt:20-21`). The CTest name keeps the original basename; the target name is the sanitized form. `NAME_WE` is deliberately NOT used - it would truncate at the first dot and collide `foo.a.cpp`/`foo.b.cpp`.
- **`qt6-template_LIB` must exist.** True only while `qt6-template_BUILD_EXECUTABLE=ON` (default, `cmake/StandardSettings.cmake:5`). If flipped OFF, `:69-73` falls back to linking `qt6-template` (the library form); if the fallback ever mismatches the actual target, tests fail to link.
- **AUTOMOC ON in the parent scope.** Set at root `CMakeLists.txt:50` before `add_subdirectory(test)` (`:311`); the test subdir does not set it itself and inherits it. Reordering these would break moc generation for every test.
- **A QPA platform plugin is reachable at runtime.** `QApplication` aborts otherwise; headless environments must set `QT_QPA_PLATFORM=offscreen`.

## Error handling & edge cases
- **Assertion failure**: `QVERIFY`/`QCOMPARE` failure -> `QTest` logs `FAIL!` and increments the count -> `main()` returns non-zero -> CTest marks the test failed. No custom error handling; the framework is the mechanism.
- **No display**: without `QT_QPA_PLATFORM=offscreen` on a headless box, `QApplication` construction aborts before any test slot runs (`qt.qpa.plugin: could not... / could not connect to display`). Every test, even the non-GUI `gslLinkTest`/`integrationSmokeTest`, hits this because `Qt6::Widgets` is linked and `QTEST_MAIN` therefore builds a `QApplication`.
- **Dashed/dotted filenames** (edge case): `name-with-dash.cpp` and `name.with.dot.cpp` now configure to valid targets (`NAME_WLE` + `MAKE_C_IDENTIFIER`), CTest names preserving the original basename — no silent mangling.
- **Boost.filesystem link edge**: `testTest.cpp:16` relies on default-constructing (not iterating) a `recursive_directory_iterator` purely to force the linker to pull Boost.filesystem; it exercises linkage, not runtime file-system behavior.
- **No timeouts or crash-recovery** are configured; a hanging test would hang CTest until CTest's default handling.

## Concurrency / async / lifecycle
- **Process isolation**: each test is a separate OS process launched by CTest; there is no shared state between test binaries, so no cross-test races.
- **Within a test**: `QTest::qExec` runs `initTestCase` -> each slot -> `cleanupTestCase` strictly sequentially on the main thread. `testTest` creates and deletes its `MainWindow` inside the single slot, so the widget lifecycle is fully bounded by that slot.
- **Parallelism**: CTest runs tests serially by default; `ctest -j<N>` can run the three binaries concurrently safely since they share no resources. None of the current tests use async signals/slots or event loops beyond `QApplication` construction.

## Performance
Effectively N/A at runtime — the three link/smoke tests each run in ~0.12s; `errorHandlingTest` is slower as it drives the modal-box funnel via a repeating timer. The only scaling concern is build cost: every test `.cpp` links the entire app static library plus Qt/Boost/GSL into its own executable, so link time grows linearly with the number of tests, and LTO (`qt6-template_ENABLE_LTO` ON by default, `cmake/StandardSettings.cmake:28`) makes each link slower. For a large app with many tests this per-binary full relink is the part that scales poorly.

## Gotchas & footguns
- **Test-name derivation is robust.** `test/CMakeLists.txt:20-21` uses `NAME_WLE` + `MAKE_C_IDENTIFIER`, so `my-test.cpp` and `my.test.cpp` produce valid targets: the CTest name keeps the original basename (`my-test` / `my.test`), the executable target uses the sanitized form. `NAME_WLE` strips only the last extension, so `foo.bar.cpp` -> `foo.bar`.
- **`_Tests` suffix asymmetry.** The CTest name is the bare basename (`gslLinkTest`) but the binary is `gslLinkTest_Tests`. Filter with the bare name: `ctest -R gslLinkTest`; run the binary with the suffix: `./build/test/gslLinkTest_Tests`.
- **Non-GUI tests still need offscreen.** `gslLinkTest` and `integrationSmokeTest` create no widgets, yet still require `QT_QPA_PLATFORM=offscreen` because `Qt6::Widgets` in `QT_COMPONENTS` makes `QTEST_MAIN` instantiate a `QApplication`.
- **`.moc` filename coupling.** The trailing `#include "<basename>.moc"` is mandatory for any `Q_OBJECT` test and must match the filename exactly; forgetting it yields "undefined vtable / no moc" errors.
- **Confusing filename `testTest.cpp`.** It is "test" + "Test", producing `testTest.moc` and CTest name `testTest`; easy to misread.
- **Unused iterator that looks like dead code.** `testTest.cpp:16` `boost::filesystem::recursive_directory_iterator it;` is never used; it is intentional link-forcing scaffolding, not a bug — do not "clean it up" without understanding it drops the Boost.filesystem link demonstration.
- **Design intent = never edit `test/CMakeLists.txt` to add a test.** Git history (`plan/ZZ-tests/feature.md`, commit `610622f`) shows `integrationSmokeTest.cpp` was added by dropping a single file and relying on the glob; the plan explicitly forbade touching `test/CMakeLists.txt` (owned by feature 01). The auto-discovery glob is the seam; editing CMake per-test defeats it. (No abandoned approaches were recorded in the plan's `dead-ends.md`, which was empty.)
- **Dependency link list is shared.** The app and every test link through the single `project_link_dependencies` helper (`cmake/Modules.cmake`), so a library added to the shared `MODULES`/`*_COMPONENTS` lists reaches both - there is no separate per-test link block to keep in sync.

## Tech debt & smells
- **Duplicated include-dir block** — `test/CMakeLists.txt:27-34` still re-implements the include-dir block from root `CMakeLists.txt:133-153`. (The link recipe is no longer duplicated: both consume the shared `project_link_dependencies` helper.)
- **Dead QML/resource plumbing for the current config** — `test/CMakeLists.txt:11-15` and the `if(${CMAKE_PROJECT_NAME}_QT_QUICK)` branch `:33-45` are always evaluated but inert while `QT_QUICK` is OFF; `TEST_RESOURCES` (`cmake/Resources.cmake:16-19`) exists only to feed them.
- **Link-forcing artifact** — `test/testTest.cpp:16` unused iterator (documented above).
- **Thin coverage** — `MainWindow`'s public/protected/private API (`func1`/`func2`/`func3`, `slot`, `signal`, static members in `src/mainwindow.h`) is never called; `testTest` only constructs and destructs the widget. No negative tests, no `_data()`-driven cases, no coverage gate enforced despite `qt6-template_ENABLE_COVERAGE` existing.

## Test surface
Framework: Qt Test (`QTEST_MAIN` + `Q_OBJECT` fixtures), orchestrated by CTest. Locations: all under `test/`. Four tests, all verified passing headless in Release.

Exact commands (all verified against `build/` with Qt 6.11.1):

- Build first (from repo root): `make build` — or raw:
  `cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release && cmake --build build --config Release`
- **Run the whole suite (verbose, headless):**
  `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -VV`
  (or `make test` from repo root, which runs exactly this). Verified: `100% tests passed, 0 tests failed out of 4` (errorHandlingTest, gslLinkTest, integrationSmokeTest, testTest).
- **Run a single test by name (verbose):**
  `cd build && QT_QPA_PLATFORM=offscreen ctest -C Release -R gslLinkTest -V`
  Verified: `100% tests passed, 0 tests failed out of 1`. (`-R` takes a regex over the bare CTest names `testTest|gslLinkTest|integrationSmokeTest|errorHandlingTest`.)
- **Run a test binary directly (bypassing CTest), optionally a single slot:**
  `QT_QPA_PLATFORM=offscreen ./build/test/testTest_Tests`  or  `QT_QPA_PLATFORM=offscreen ./build/test/testTest_Tests TestQString::toUpper`

Coverage note: `errorHandlingTest` now behaviorally exercises the exception funnel (the `errorMessageHandler` Critical->`AppException` throw, the non-throwing Info/Warning/Debug paths, and `AppException` `what`/`clone`/`raise`/`errorType`). Still untested: `main.cpp`'s catch ladder end-to-end, all real `MainWindow` behavior (methods, slots, signals), and anything QML. There is no `ErrorTypeStr[]` array to keep in sync (the string map is the `operator<<` switch).

## Extension points
- **Add a test**: create `test/<name>.cpp` with a `QObject` fixture, one or more `private slots`, `QTEST_MAIN(<Fixture>)`, and (if `Q_OBJECT` is declared) `#include "<name>.moc"` at the bottom; reconfigure CMake. It is auto-discovered by `cmake/Sources.cmake:6-7`, built as `<name>_Tests`, and registered as CTest test `<name>`. Dashes and dots in the basename are fine (`NAME_WLE` + `MAKE_C_IDENTIFIER` handle them).
- **Test a new part of the app**: because tests link `qt6-template_LIB`, any symbol reachable from `SOURCE_FILES` is directly callable from a test — just `#include` the relevant `src/` header (the `src/` and `src/qml` include dirs are already on the path, `test/CMakeLists.txt:28-30`).
- **Add a test-only dependency**: add to the shared `MODULES`/`QT_COMPONENTS`/`BOOST_COMPONENTS` lists in `cmake/Modules.cmake`; the `project_link_dependencies` helper links them into the app and every test alike (there is no separate per-test link block).
- **Data-driven tests**: use Qt Test's `<slot>_data()` companion slots and `QFETCH` — no harness change needed.
- **Parallelize CI**: append `-j<N>` to the `ctest` command; the process-isolated tests are safe to run concurrently.
