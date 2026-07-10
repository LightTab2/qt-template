# Build System

C++17 enforced globally. Qt6 and Boost.

## Dependencies

- **Two targets** from one source set: executable `qt6-template` plus static library `qt6-template_LIB`. Tests link the library, not the executable.
- **Conan** (`conan/conanfile.txt`) provides `boost/1.91.0` and `ms-gsl/4.2.2`. ms-gsl (`Microsoft.GSL::GSL`) is linked to the app, the library, and the test targets, so a source may `#include <gsl/gsl>` (see `test/gslLinkTest.cpp`).
- **Qt6** is resolved with `find_package(Qt6 ...)` (not via Conan). CI targets Qt 6.11 (6.8 LTS is the documented fallback).

## Makefile shortcuts

`make` is the convenience entrypoint over raw cmake/conan/ctest. Frozen target set (12):

- `make help` - list targets (default).
- `make conan` - install deps with Conan (Debug + Release).
- `make configure` - configure CMake via the Conan toolchain.
- `make build` - build (depends on `configure`).
- `make run` - build then run the executable.
- `make test` - run the test suite headless (`QT_QPA_PLATFORM=offscreen`).
- `make docs` / `make docs-serve` / `make docs-clean` - build docs / serve on `http://localhost:8000` / remove generated docs.
- `make format` - clang-format sources in place.
- `make tidy` - clang-tidy over sources (needs a configured build).
- `make clean` - remove build directories.

`make configure` requires the Conan toolchain, so run `make conan` first; when the toolchain is missing it fails fast with `error: conan toolchain not found at $(TOOLCHAIN); run 'make conan' first`. `make docs-serve` delegates to `scripts/serve_doxygen.sh`, which honors `PORT` (default 8000) and self-builds missing docs.

## Configure and Build

```bash
cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

## Run Tests

```bash
cd build && ctest -C Release -VV
```

Tests require a display; use `QT_QPA_PLATFORM=offscreen` for headless environments.

Smoke check: `QT_QPA_PLATFORM=offscreen ./build/qt6-template --self-test` constructs and shows `MainWindow`, quits after one event-loop pass, and exits 0 (offscreen-safe). CI also runs `actionlint` over the workflow files and `clang-format --dry-run --Werror` over `src` and `test`.

## Sanitizers and Coverage

`cmake/StandardSettings.cmake` defines build options (prefix `qt6-template_`), pass at configure time with `-D<name>=ON`:

- `qt6-template_ENABLE_ASAN` - AddressSanitizer (OFF).
- `qt6-template_ENABLE_UBSAN` - UndefinedBehaviorSanitizer (OFF), e.g. `-Dqt6-template_ENABLE_UBSAN=ON`.
- `qt6-template_ENABLE_COVERAGE` - gcov / llvm-cov instrumentation (OFF).
- `qt6-template_ENABLE_LTO` - interprocedural / link-time optimization (ON by default).
- `qt6-template_WARNINGS_AS_ERRORS` - treat compiler warnings as errors (OFF).

## Documentation

`make docs` (or `bash scripts/run_doxygen.sh` directly) builds the Doxygen HTML into `docs/html`. The script pins **Doxygen 1.17.0** (never resolves "latest"), fetches Qt tag files for cross-links into `doxygen/qt-tags` (a gitignored local cache fetched on demand), renders with the vendored `doxygen-style-revamped` theme, and copies webfonts into `docs/html/fonts/` so the CSS `url('fonts/...')` paths resolve.

- `doxygen/Doxyfile` - base config (public API surface).
- `doxygen/Doxyfile_dev` - `@INCLUDE`s `Doxyfile` and adds private/internal members; this is the config the script drives.
- `doxygen/header.html` - the single HTML header used by both configs.

# Architecture

The project builds **two targets** from the same sources: an executable (the UI app) and a static library. Tests link against the library, not the executable, keeping them independent.

## Exception Handling

`src/Exceptions/Exceptions.h` defines:
- `AppException` - base custom exception inheriting `QException`; constructor `AppException(const char* msg, ErrorType errorType = ErrorType::General)` (msg first), with a public `const ErrorType errorType` member and `raise()` / `clone()` / `what()`.
- `ErrorType` enum - categories in XXZZ format (category/subcategory). The values are decimal, so never write leading-zero literals (`0108` is parsed as octal and fails to compile).

Error-type strings come from the `switch` inside `QDebug operator<<(QDebug, const ErrorType&)` in `src/Exceptions/Exceptions.cpp` (there is no lookup array). Extending `ErrorType` means adding the enum value AND a matching `case` to that switch.

The active `main()` catches four tiers - `AppException` -> `QException` -> `std::exception` -> `catch (...)`; each tier logs to `stderr`, shows a `QMessageBox`, and returns `EXIT_FAILURE` (no rethrow). The `_DEBUG` macro controls debug-only logging on all platforms.

## Testing Pattern

Each `.cpp` file in `test/` becomes a standalone Qt Test executable via `QTEST_MAIN`. Tests are discovered and run through CTest. Add a new test by creating a `.cpp` file with `QTEST_MAIN` - `cmake/Sources.cmake` picks it up automatically.

## Qt Conventions

- `AUTOMOC`, `AUTOUIC`, and `AUTORCC` are enabled - declare `Q_OBJECT` in headers and CMake handles MOC/UIC/RCC automatically.
- `.ui` files go in `src/` and generate `ui_*.h` headers.
- QML files are in `src/qml/`; conditional Qt Quick compilation is supported via CMake options.
- Use `/// \brief` and `/// \param` Doxygen style (see `src/mainwindow.h` for reference).

# AI-Assisted Development

The repo vendors a workflow skill toolkit under `.claude/skills/`. The parallel chain runs:

- **Capture**: `/sketch` or `/todo` turn a rough idea into requirements in `NextThingsToDo.md`.
- **Plan**: `/parallel-plan[-opus]` decomposes the work into a `plan/` folder; `/review-plan[-opus]` gap-checks it and `/fix-plan[-opus]` patches the plan.
- **Build**: `/execute-plan[-opus]` builds the plan via an agent hierarchy.
- **Audit**: `/review-implementation[-opus]` audits the code and `/fix-implementation[-opus]` patches it.
- **Support**: `/codebase-summary[-opus]` maps the repo and `/handoff` recaps a session.

`/ship` (and `/ship-opus`) is a **standalone, single-thread, spec-driven** build loop over one `SPEC.md` at repo root: grill -> spec -> research -> review -> build -> check. It is NOT part of the parallel `/parallel-plan` chain - it routes genuinely parallel multi-domain work out to `/parallel-plan`, and is the lightweight one-file loop for small-to-medium features.

Optional MCP companions: **token-savior** for symbol-level find/read/edit.
