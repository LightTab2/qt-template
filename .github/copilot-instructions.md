# Project Architecture

This is a **Qt6 desktop application** built with CMake and C++17. The project generates both an executable (UI application) and a static library from the same source, enabling code reuse in tests.

**Key structural decisions:**
- **Dual-target build**: Each source file compiles into both the executable and library to allow tests to link against core logic
- **Modular dependency management**: Uses Conan for external libraries (boost, GSL) and Qt's built-in CMake integration for Qt6 components
- **Test isolation**: Tests live in `test/` and run as separate executables that use the library, not the main app

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

# Code Organization and Patterns

## Directory Structure
- `src/`: Application source code
  - `main.cpp`: Entry point with comprehensive exception handling
  - `mainwindow.{h,cpp,ui}`: Qt Designer UI and main window class
  - `Exceptions/`: Custom exception types and error handling utilities
  - `qml/`: Placeholder for QML files (if Qt Quick is used)
- `test/`: Unit tests—each `test/*.cpp` generates a separate executable via CMake's loop
- `pages/`: Documentation markdown (e.g., `index.md`)
- `doxygen/`: Doxygen configuration and custom theming

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
- **Conan** (package manager)
- **Qt6**
- **Boost**

Adding new Conan packages: edit `conan/conanfile.txt`, run install script, then reference in CMakeLists.txt with `find_package()` and `target_link_libraries()`.

# Common AI Agent Tasks

## Adding a new Qt component
1. Edit `cmake/Modules.cmake`: add to `QT_COMPONENTS` list (e.g., `Quick` for QML)
2. CMake regeneration auto-configures AUTOMOC/AUTOUIC for new MOC usage
3. If using QML + Quick, test/CMakeLists.txt auto-enables `qt_add_qml_module()`

## Adding a source file
Files matching `src/**/*.{cpp,h,ui}` auto-discovered — no CMakeLists.txt edit needed. Rebuilding CMake triggers re-GLOB.

## Adding a test
Create `test/myTest.cpp`, rebuild CMake — automatically generates `myTest_Tests` executable.

## Adding Libraries
For detailed instructions on adding different types of libraries (Qt6 components, header-only libraries, Conan packages with and without components), see [`pages/adding-libraries.md`](./instructions/addLibrary.instructions.md).