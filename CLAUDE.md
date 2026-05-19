# Build System

C++17 enforced globally. Qt6 and Boost.

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

# Architecture

The project builds **two targets** from the same sources: an executable (the UI app) and a static library. Tests link against the library, not the executable, keeping them independent.

## Exception Handling

`src/Exceptions/Exceptions.h` defines:
- `AppException` - base custom exception inheriting `QException`
- `ErrorType` enum - categories in XXZZ format (category/subcategory)
- `ErrorTypeStr[]` - string representations; **must be extended in sync with `ErrorType`**

`main.cpp` catches three tiers: `AppException` → `QException` → `std::exception`, logs to `stderr` (Debug only), and shows a `QMessageBox`. The `_DEBUG` macro controls debug-only logging on all platforms.

## Testing Pattern

Each `.cpp` file in `test/` becomes a standalone Qt Test executable via `QTEST_MAIN`. Tests are discovered and run through CTest. Add a new test by creating a `.cpp` file with `QTEST_MAIN` - `cmake/Sources.cmake` picks it up automatically.

## Qt Conventions

- `AUTOMOC`, `AUTOUIC`, and `AUTORCC` are enabled - declare `Q_OBJECT` in headers and CMake handles MOC/UIC/RCC automatically.
- `.ui` files go in `src/` and generate `ui_*.h` headers.
- QML files are in `src/qml/`; conditional Qt Quick compilation is supported via CMake options.
- Use `/// \brief` and `/// \param` Doxygen style (see `src/mainwindow.h` for reference).
