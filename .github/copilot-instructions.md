# Project Architecture

This is a **Qt6 desktop application** built with CMake and C++17. The project generates both an executable (UI application) and a static library from the same source, enabling code reuse in tests.

# Build and Development Workflow

## Initial Setup
```bash
# 1. Install Conan dependencies (required once, run from repo root)
./conanLibrariesInstall.sh

# 2. Configure CMake with Ninja generator
cmake . -G Ninja -B build -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release

# 3. Build the project
cmake --build build --config Release
```

## CMake Configuration Files
- `cmake/Modules.cmake`: Defines `QT_COMPONENTS` and external library dependencies
- `cmake/Sources.cmake`: Dynamically collects all `src/*.cpp`, `src/*.h`, `src/*.ui` and `test/*.cpp` via `GLOB_RECURSE`
- `cmake/StandardSettings.cmake`: Compiler settings and C++17 standard enforcement
- `cmake/CompilerWarnings.cmake`: Per-target warning configuration

When adding dependencies: modify `conan/conanfile.txt` for external libraries or `cmake/Modules.cmake` for Qt components, then re-run Conan.

# Code Patterns

## Exception Handling Pattern
The template enforces exception safety at multiple levels:
1. **main.cpp** catches and logs four exception tiers (AppException, QException, std::exception, and a catch-all) before showing MessageBox, then returns EXIT_FAILURE
2. **Custom exceptions** defined in `src/Exceptions/Exceptions.h` inherit from `QException`
3. Each exception carries an `ErrorType` enum value; its human-readable string comes from the `QDebug operator<<(QDebug, const ErrorType&)` switch in `src/Exceptions/Exceptions.cpp`

When adding a new error category, add an `ErrorType` enum value AND a matching `case` to that switch. `ErrorType` values are XXZZ decimal - never use leading-zero literals, which are octal.

## Qt-Specific Conventions
- **AUTOMOC/AUTOUIC enabled**: CMake automatically handles MOC preprocessing and UI file compilation - declare `Q_OBJECT` in header files
- **Doxygen comments**: Use `/// \brief` and `/// \param` style documentation (visible in `src/mainwindow.h`)

## Testing Pattern
Tests are executable-based, not linked into the app. Each test file becomes an independent Qt Test executable that can be run standalone.

# Compiler and Platform Considerations

- **C++ Standard**: C++17 enforced globally (`CMAKE_CXX_STANDARD = 17`)
- **Debug macro**: On Unix, `_DEBUG` is set for Debug builds (mirrors MSVC behavior for consistency)

## External Dependencies
- **Qt6**
- **Boost**