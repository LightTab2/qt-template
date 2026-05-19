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
1. **main.cpp** catches and logs three exception categories (AppException, QException, std::exception) before showing MessageBox
2. **Custom exceptions** defined in `src/Exceptions/Exceptions.h` inherit from `QException`
3. Each exception has an `ErrorType` enum mapping to string constants for consistent error messages

When adding new exceptions, extend `ErrorType` enum and `ErrorTypeStr` array together.

## Qt-Specific Conventions
- **AUTOMOC/AUTOUIC enabled**: CMake automatically handles MOC preprocessing and UI file compilation—declare `Q_OBJECT` in header files
- **Doxygen comments**: Use `/// \brief` and `/// \param` style documentation (visible in `src/mainwindow.h`)

## Testing Pattern
Tests are executable-based, not linked into the app. Each test file becomes an independent Qt Test executable that can be run standalone.

# Compiler and Platform Considerations

- **C++ Standard**: C++17 enforced globally (`CMAKE_CXX_STANDARD = 17`)
- **Debug macro**: On Unix, `_DEBUG` is set for Debug builds (mirrors MSVC behavior for consistency)
- **MSVC runtime**: Windows uses multithreaded DLL runtime (`MultiThreadedDLL` for Release, `MultiThreadedDebugDLL` for Debug)

## External Dependencies
- **Qt6**
- **Boost**