[![Actions Status](https://github.com/lighttab2/qt-template/workflows/macOS/badge.svg)](https://github.com/lighttab2/qt-template/actions/workflows/macos.yml)
[![Actions Status](https://github.com/lighttab2/qt-template/workflows/Windows/badge.svg)](https://github.com/lighttab2/qt-template/actions/workflows/windows.yml)
[![Actions Status](https://github.com/lighttab2/qt-template/workflows/Ubuntu/badge.svg)](https://github.com/lighttab2/qt-template/actions/workflows/ubuntu.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/lighttab2/qt-template)](https://github.com/lighttab2/qt-template/releases)

# [Project name]
[Project logo]

[Cool PNGs to attract people]

<p align="center">
<img src="pages/doxygen_dark.png" alt="Doxygen example" width="49.5%" title="Doxygen Dark Theme"/>
<img src="pages/doxygen_dark2.png" alt="Doxygen example 2" width="49.5%" title="Doxygen Dark Theme"/>
</p>

[Project short info]

[Project usage example GIFs]

## Install

<details><summary>Prerequisites</summary>

* **[CMake v3.21+](https://cmake.org/)**

* **[Python 3](https://www.python.org/)**
    * **Conan** &ndash; `pip install conan`

* **[Qt 6](https://www.qt.io/)**

* **C++ compiler that can compile Qt6** &ndash; needs to support the **C++17** standard. Lists of viable compilers:
    * [Linux](https://doc.qt.io/qt-6/linux.html)
    * [Windows](https://doc.qt.io/qt-6/windows.html)
    * [macOS](https://doc.qt.io/qt-6/macos.html)

<hr>
</details>

### Install packages using *Conan*:

```bash
conan install conan/ --build=missing --settings=build_type=Debug
conan install conan/ --build=missing --settings=build_type=Release
```

### [Simply run *CMake*:](https://cmake.org/runningcmake/)

<details><summary>Bash</summary>

```bash
cmake . -G [generator] -T [toolset] --build [PathToBuiltProject]
```

Example:

```bash
cmake . -G "Visual Studio 16 2019" -T v143 -Bbuild
```

<hr>
</details>

<details><summary>GUI</summary>

The procedure is the standard one, but there are three things to be way of.

**In-source** builds are not allowed so these directories must differ:
<p align="center">
<img src="pages/cmake.png" alt="CMake screenshot" width="55%"/>
</p>

You need to provide **architecture** and **toolkit**. If you leave them blank, project **generation** will likely fail. Also select option to specify the **toolchain file**:

<p align="center">
<img src="pages/cmake2.png" alt="CMake settings screenshot" width="55%"/>
</p>

If you did not tinker with *Conan*, the **toolchain file** should be found at `conan/conan_toolchain.cmake`. 

<p align="center">
<img src="pages/cmake3.png" alt="CMake settings screenshot" width="35%"/>
</p>

<hr>
</details>

### Build the project

You can use your local *IDE* or *CMake* again:

```bash
cmake --build [pathToBuiltProject] --config [configuration] -j4 -DCMAKE_TOOLCHAIN_FILE=[pathToConanToolchainFile]
```

Example:

```bash
cmake --build build --config release -j4 -DCMAKE_TOOLCHAIN_FILE=conan/conan_toolchain.cmake
```

## Features
[List of features]

## Troubleshooting

<details><summary>Add a new <b>library</b></summary>

### Qt6 library
Simply modify `cmake/Modules.cmake`:

```cmake
set(QT_COMPONENTS Core {Other Qt6 libraries you want})
```

Example:

```cmake
set(QT_COMPONENTS Core Gui Widgets)
```

### Other libraries
#### Step 1.
Modify `conan/conanfile.txt`:

```ini
[requires]
{Other libraries}
{New library's name from https://conan.io/center/}
```

Example:

```ini
[requires]
zlib/1.2.11
libcurl
```

Remember to run *Conan* after the changes:

```bash
conan install conan/ --build=missing --settings=build_type=Debug
conan install conan/ --build=missing --settings=build_type=Release
```

If the library cannot be found on [ConanCenter](https://conan.io/center/), you could try going for [Artifactory](https://docs.conan.io/2/), but this requires some effort. You can always use plain *CMake* and modify `CMakeLists.txt`, [ChatGPT](https://chat.openai.com/) might help with such quick fixes.

#### Step 2.

Now the library should be available but **might not be linked to the *CMake* project**. \
Check if the library has **components**. Libraries with **components** are libraries like *Qt6* or *Boost*, in which you can choose to use **a few of their all features**.

<ul style="list-style-type:none;">
<li><details><summary>Header-only library</summary>

Nothing needs to be done. Header-only libraries are already added in *Conan* toolchain file.

<hr>
</details>
</li>

<li><details><summary>Library w/o components</summary>

Modify `cmake/Modules.cmake`:

```cmake
set(MODULES {Libraries})
```

Example:

```cmake
set(MODULES ZLIB libcurl)
```

That's it!
<hr>
</details>
</li>

<li><details><summary>Library with components</summary>
This is quite some work :<

Add to `cmake/Modules.cmake`:

```cmake
set({NEW_VARIABLE_WITH_COMPONENTS} {COMPONENTS})
```

Example:

```cmake
set(BOOST_COMPONENTS filesystem)
```

Modify `CMakeLists.txt` and after line `7`: `include(cmake/Modules.cmake)` add following code:

```cmake
foreach(library IN LISTS {NEW_VARIABLE_WITH_COMPONENTS})
    find_package({LIBRARY_NAME} COMPONENTS ${library} REQUIRED)
endforeach()
```

Example:

```cmake
foreach(library IN LISTS BOOST_COMPONENTS)
    find_package(Boost COMPONENTS ${library} REQUIRED)
endforeach()
```

In the **same file**, after line `135`: `# Link libraries` add following code:

```cmake
foreach(library IN LISTS {NEW_VARIABLE_WITH_COMPONENTS})
    target_link_libraries(${PROJECT_NAME} PRIVATE {LIBRARY_NAME}::${library})
    if(${PROJECT_NAME}_BUILD_EXECUTABLE)
        target_link_libraries(${PROJECT_NAME}_LIB PRIVATE {LIBRARY_NAME}::${library})
    endif()
endforeach()
```

Example:

```cmake
foreach(library IN LISTS BOOST_COMPONENTS)
    target_link_libraries(${PROJECT_NAME} PRIVATE Boost::${library})
    if(${PROJECT_NAME}_BUILD_EXECUTABLE)
        target_link_libraries(${PROJECT_NAME}_LIB PRIVATE Boost::${library})
    endif()
endforeach()
```

You should also link the library to the **test** projects. To do that, modify `test/CMakeLists.txt` and after line `53`: `# Link libraries` add following code:

```cmake
    foreach(library IN LISTS {NEW_VARIABLE_WITH_COMPONENTS})
        target_link_libraries(${test_name}_Tests PRIVATE {LIBRARY_NAME}::${library})
    endforeach()
```

Example:

```cmake
    foreach(library IN LISTS BOOST_COMPONENTS)
        target_link_libraries(${test_name}_Tests PRIVATE Boost::${library})
    endforeach()
```

<hr>
</details>
</li>
</ul>
<hr>
</details>

<details><summary>Change the project's <b>name</b></summary>

To change the project's name, you must correct a few entries:
 
<ul style="list-style-type:none;">
<li><details><summary><code>CMakeLists.txt</code></summary>
By default, the file starts with:

```cmake
cmake_minimum_required(VERSION 3.21)

project("qt-template"
        LANGUAGES CXX)
```

Change `"qt-template"` to the name of your project.
        
Example:

```cmake
cmake_minimum_required(VERSION 3.21)

project("myproject"
        LANGUAGES CXX)
```
    
If you host your project on a *GitHub* repository and wish to use *GitHub Actions* for automatic deployment, you must provide a name that matches the **repository name**. It has to be **lowercase**. Otherwise, you need to change `${{ steps.repoName.outputs.name }}` to your **project's executable/library name** (it is the **CMake project name**, unless you tinkered with `CMakeLists.txt`) in these files:
* `.github/workflows/macos.yml`
* `.github/workflows/ubuntu.yml`
* `.github/workflows/windows.yml`

If the name contains *whitespace characters*, you will need to enclose the entire entry in either `"` or `'`. \
Example:

```yaml
files: build/install/${{ steps.repoName.outputs.name }}_macOS_${{ steps.versionTag.outputs.tag }}.tar.gz
```

Becomes:

```yaml
files: "build/install/Parrots and Cats_macOS_${{ steps.versionTag.outputs.tag }}.tar.gz"
```

<hr>
</details>
</li>

<li><details><summary><code>config.desktop</code></summary>

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

<hr>
</details>
</li>
</ul>
<hr>
</details>

<details><summary>Setup a <b>Qt Quick</b> project</summary>

Adding the "Quick" module to `cmake/Modules.cmake` will activate additional *CMake* steps for QML processing:

```cmake
set(QT_COMPONENTS Core [...] Quick)
```

The `.qml` files should be placed in `src/qml` (creating subdirectories is possible) and they can be accessed from `qrc:/qt/qml/{project_name}/{relativePathToFile}`.

Example for a file `src/qml/birds/Bird1.qml` and project name `parrot_songs`: \
`qrc:/qt/qml/parrot_songs/birds/Bird1.qml`.

There is a commented snippet in `src/main.cpp` with `int main(int argc, char* argv[])` definition for **Qt Quick**, which contains example of accessing a QML file.

<hr>
</details>

<details><summary><i>Qt6</i> is <b>not found</b>, despite being installed</summary>

Ensure that these **environment variables** are set properly:

* **Qt6_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6`<br/>Example: `C:/Qt/6.5.1/msvc2019_64/lib/cmake/Qt6`

* **Qt6GuiTools_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6GuiTools`<br/>Example: `/usr/lib/x86_64-linux-gnu/6.5.1/clang_64/lib/cmake/Qt6GuiTools`

* **Qt6CoreTools_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6CoreTools`<br/>Example: `D:/Qt/6.3/msvc2019_64/lib/cmake/Qt6CoreTools`

<hr>
</details>

<details><summary><b>Missing</b> or <b>wrong architecture</b> libraries | <i>Conan</i> profile errors</summary>

Ensure `conan/conanfile.txt` has listed all the needed libraries under `[requires]` section.
Run:

```bash
conan install conan/ --build=missing --settings=build_type=Debug
conan install conan/ --build=missing --settings=build_type=Release
```

In case of a **wrong architecture** of the libraries and other possible **profile errors**, read: [https://docs.conan.io/2.0/reference/config_files/profiles.html](https://docs.conan.io/2.0/reference/config_files/profiles.html)<br/>
If you don't have a profile, create one:

```bash
conan profile new default --detect
```

<hr>
</details>

<details><summary>Change the <b>icon</b> of the project</summary>

Put your **icon image** in **PNG** format into a folder `icon/` and **rename** it, so it matches this convention:

```
icon_[width]x[height].png
```

Example:

```
icon_256x256.png
```

The resolution should be one of these:
* 16x16
* 32x32
* 48x48
* 64x64
* 128x128
* 256x256

Further below, I will mention some *scripts* that use [ImageMagick](https://imagemagick.org/index.php), so you need to install it, if you want to use them. On *Ubuntu*, it can be done by:
```bash
sudo apt install imagemagick
```

Beware that depending on your **OS version**, you can get either *ImageMagick 6* or *ImageMagick 7*. *Unix scripts* contain `[script]_ImageMagick7.sh` versions, in case you did not obtain *ImageMagick 6*, but *ImageMagick 7*.

You can provide an icon with **any** resolution, and it will be **rescaled** to the other **valid resolutions**, if you use the script:
<ul style="list-style-type:none;">
<li><details><summary>Windows</summary><code>/icon/WinScripts/rescale.bat</code></details></li>
<li><details><summary>Unix</summary><code>/icon/UnixScripts/rescale.sh</code> or <code>/icon/UnixScripts/rescale_ImageMagick7.sh</code> </details></li>
</ul>

If there are multiple icons with **different resolutions**, the **highest resolution** will be used to create other **valid** icons. They will **overwrite** any already existing ones! If you want to use **different icons** for **different resolutions**, provide them manually and do not use the script.

This is sufficient for *Linux*, but there are two other scripts, so the *Windows* and *macOS* applications will have icons too.

To generate an icon for *Windows*, use:
<ul style="list-style-type:none;">
<li><details><summary>Windows</summary><code>/icon/WinScripts/createIco.bat</code></details></li>
<li><details><summary>Unix</summary><code>/icon/UnixScripts/createIco.sh</code> or <code>/icon/UnixScripts/createIco_ImageMagick7.sh</code></details></li>
</ul>

*macOS* icon is slightly tricky to create on *Windows*, as we do not have a ready script. I recommend using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) or another form of virtualization (i.e.: [VirtualBox](https://www.virtualbox.org/) or [Docker](https://www.docker.com/)) and running the *Unix script* `/icon/UnixScripts/createIcns.sh`.\
If you are on *macOS*, you can do this the **native way**, using [iconutil](https://stackoverflow.com/questions/12306223/how-to-manually-create-icns-files-using-iconutil). Otherwise, run `/icon/UnixScripts/createIcns.sh`, which requires `png2icns` library. On *Ubuntu* you can install it by:

```bash
sudo apt install icnsutils
```
    
<hr>
</details>

<details><summary>Docs shouldn't contain <b>private</b> members and <b>source code</b></summary>

If your project is a library, you might not want to add the **private** and **protected** members to your documentation. Editing one line in `.github/workflows/doxygen.yml` can change this behaviour. Find this step:

```yaml
- name: Generate documents and deploy
    uses: DenverCoder1/doxygen-github-pages-action@v1.3.0
    with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        branch: docs
        config_file: doxygen/Doxyfile_dev
```

And change it to:

```yaml
- name: Generate documents and deploy
    uses: DenverCoder1/doxygen-github-pages-action@v1.3.0
    with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        branch: docs
        config_file: doxygen/Doxyfile
```

 If you want to further customize output and its display, all files related to documentation are stored in `/doxygen` folder. 

<hr>
</details>

<details><summary>"/bin/bash^M: bad interpreter: No such file or directory"</summary>

If you downloaded the project on *Windows* and try to run these scripts in Unix, you might encounter:  
*`-bash: ./createIcns.sh: /bin/bash^M: bad interpreter: No such file or directory`*

Run `icon/WinScripts/fixUnixScripts.ps1`  
Or some tool like **dos2unix**.
On *Ubuntu* you can install it by:

```bash
sudo apt install dos2unix
```

And then simply run (assuming you are at `qt-template/`):

```bash
dos2unix ./icon/UnixScripts/*.sh
```

<hr>
</details>

<details><summary>Add/change/remove custom filter </summary>

At line `174` of `CMakeLists.txt` you can modify following code for **filters** to change or remove them:

<details><summary>The code</summary>

```cmake
 # For resource files 
source_group("Resources" FILES 
             "${CMAKE_BINARY_DIR}/.rcc/resources.qrc"
             "${CMAKE_BINARY_DIR}/.rcc/qrc_resources.cpp")
file(GLOB_RECURSE SOURCES "*.rc" "*.qrc")
foreach(SOURCE ${SOURCES})
    source_group("Resources" FILES ${SOURCE})
endforeach()
  # Resources defined in cmake/Resources.cmake
foreach(SOURCE ${RESOURCES})
    source_group("Resources" FILES ${SOURCE})
endforeach()

 # For source code
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.h" "src/*.ui")
foreach(SOURCE ${SOURCES})
    get_filename_component(SOURCE_DIR "${SOURCE}" DIRECTORY)
    file(RELATIVE_PATH SOURCE_PATH "${CMAKE_CURRENT_SOURCE_DIR}" ${SOURCE_DIR})
    string(REPLACE "src" "Source Files" SOURCE_PATH "${SOURCE_PATH}")
    source_group("${SOURCE_PATH}" FILES ${SOURCE})
endforeach()

 # For autogenerated by Qt ui_[name].h files for every src/*.ui file
file(GLOB_RECURSE SOURCES "src/*.ui")
foreach(SOURCE ${SOURCES})
    get_filename_component(FILE_NAME ${SOURCE} NAME_WE) # Extract file name without extension
    file(RELATIVE_PATH SOURCE_PATH "${CMAKE_CURRENT_SOURCE_DIR}" ${SOURCE})
    string(REPLACE "${FILE_NAME}.ui" "" FILE_PATH "${SOURCE_PATH}" )
    source_group("Autogen/ui/${FILE_NAME}" FILES 
                 "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/include_Debug/${FILE_PATH}ui_${FILE_NAME}.h" 
                 "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/include_MinSizeRel/${FILE_PATH}ui_${FILE_NAME}.h"
                 "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/include_Release/${FILE_PATH}ui_${FILE_NAME}.h" 
                 "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/include_RelWithDebInfo/${FILE_PATH}ui_${FILE_NAME}.h")
endforeach()

 # For autogenerated by Qt stamp files
source_group("Autogen/autouic" FILES
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_LIB_autogen/autouic_Debug.stamp"
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_LIB_autogen/autouic_MinSizeRel.stamp" 
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_LIB_autogen/autouic_Release.stamp" 
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_LIB_autogen/autouic_RelWithDebInfo.stamp" )

 # For autogenerated by Qt stamp files
source_group("Autogen/autouic" FILES
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/autouic_Debug.stamp"
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/autouic_MinSizeRel.stamp" 
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/autouic_Release.stamp" 
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/autouic_RelWithDebInfo.stamp" )

 # For autogenerated by Qt MOC files
source_group("Autogen/moc" FILES 
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/mocs_compilation_Debug.cpp"
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/mocs_compilation_MinSizeRel.cpp"
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/mocs_compilation_Release.cpp"
             "${CMAKE_BINARY_DIR}/${PROJECT_NAME}_autogen/mocs_compilation_RelWithDebInfo.cpp")

source_group("CMake Rules" FILES "CMakeLists.txt")
```

</details>

You can add your own filters after line `232` in `CMakeLists.txt`, by adding:

```cmake
source_group("[FILTER_NAME]" FILES "[FILE_PATHS]")
```

Example:

```cmake
source_group("birds" FILES "src/flamingo.ui" "src/Birds/crow.h")
```

<hr>
</details>

## Contributing

This project follows these [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), and it would be fun if you followed them too. If you don't, someone will correct your code. An ugly contribution is better than no contribution. **Thanks**!

## License

This project is licensed under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/); see the
[LICENSE](LICENSE) file for details.
It also uses the [Qt](https://www.qt.io/) library and possibly some of its additional modules that are licensed under the [LGPL](https://www.gnu.org/licenses/lgpl-3.0.en.html), but **none** of its code is present in this repository. Also note that *Qt* itself uses [other third-party libraries](https://doc.qt.io/qt-6/licenses-used-in-qt.html) under **different** license terms.
