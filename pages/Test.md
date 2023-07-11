[TOC]
# [Project name]
## Prerequisites

* **CMake v3.21+** &ndash; found at [https://cmake.org/](https://cmake.org/)

* **Python 3** &ndash; found at [https://www.python.org/](https://www.python.org/)
    * **Conan** &ndash; `pip install conan`

* **Qt 6** &ndash; found at [https://www.qt.io/](https://www.qt.io/)

* **C++ compiler that can compile Qt** &ndash; needs to support the **C++17** standard:
    * [Linux](https://doc.qt.io/qt-6/linux.html)
    * [Windows](https://doc.qt.io/qt-6/windows.html)
    * [macOS](https://doc.qt.io/qt-6/macos.html)

## Install

### Install packages using 

```bash
conan install conan/ --build=missing
```

```bash
cmake . -G [generator] -T [toolset] --build [PathToBuiltProject]
```

Example:

```bash
cmake . -G "Visual Studio 16 2019" -T v143 -Bbuild
```

### Build the project

You can use your local *IDE* or *CMake* again:

```bash
cmake --build [pathToBuiltProject] --config [configuration] -j4 -DCMAKE_TOOLCHAIN_FILE=[pathToConanToolchainFile]
```

Example:

```bash
cmake --build build --config release -j4 -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake
```
# Second

## Features
[List of features]

## Troubleshooting

If this is not a *Qt* library, modify _conan/conanfile.txt_:

```ini
[requires]
{...Other libraries...}
{Your Library Name Here Taken From https://conan.io/center/}

[generators]
CMakeDeps
CMakeToolchain
```

Example:

```ini
[requires]
zlib/1.2.11
libcurl

[generators]
CMakeDeps
CMakeToolchain
```

Remember to run *Conan* after the changes:

```bash
conan install conan/ --build=missing -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake
```

Now they are available but not added to the *CMake* project itself. To do that, **modify** _cmake/Modules.cmake_:

```cmake
set(Modules {Libraries From Conan})
set(QtModules {Qt Modules})
```

Example:

```cmake
set(Modules ZLIB libcurl)
set(QtModules Widgets Network)
```

If your library cannot be found on *ConanCenter*, you could try going for [Artifactory](https://docs.conan.io/2/), but this requires some effort. You can always use plain *CMake* and modify `CMakeLists.txt`, preferably including another *CMake* file in `cmake` directory.


Ensure that these **environment variables** are set properly:

* **Qt6_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6`<br/>example: `C:/Qt/6.5.1/msvc2019_64/lib/cmake/Qt6`

* **Qt6GuiTools_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6GuiTools`<br/>example: `/usr/lib/x86_64-linux-gnu/6.5.1/clang_64/lib/cmake/Qt6GuiTools`

* **Qt6CoreTools_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6CoreTools`<br/>example: `D:/Qt/6.3/msvc2019_64/lib/cmake/Qt6CoreTools`

Ensure `conan/conanfile.txt` has listed all the needed libraries under `[requires]` section.
Run:

```bash
conan install conan/ --build=missing
```

In case of a **wrong architecture** of the libraries and other possible **profile errors**, read: [https://docs.conan.io/2.0/reference/config_files/profiles.html](https://docs.conan.io/2.0/reference/config_files/profiles.html)<br/>
If you don't have a profile, create one:

```bash
conan profile new default --detect
```

By default, the file starts with:

The `Exec` option should contain the **project's executable/library name** (it is **CMake project name**, unless you tinkered with `CMakeLists.txt`), while the `Name` is up to your choice. 

Change these entries:

```ini
Name=Qt Template
Exec=qt-template
```

Example:

```ini
Name=Parrots That Sing
Exec=birds-and-stuff
```


## Contributing

This project follows these [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), and it would be fun if you followed them too. If you don't, someone will correct your code. An ugly contribution is better than no contribution. **Thanks**!

## License

This project is licensed under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/); see the
[LICENSE](LICENSE) file for details.
It also uses the [Qt](https://www.qt.io/) library and possibly some of its additional modules that are licensed under the [LGPL](https://www.gnu.org/licenses/lgpl-3.0.en.html), but **none** of its code is present in this repository. Also note that *Qt* itself uses [other third-party libraries](https://doc.qt.io/qt-6/licenses-used-in-qt.html) under **different** license terms.
