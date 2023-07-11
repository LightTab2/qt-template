[![Actions Status](https://github.com/lighttab2/qt-template/workflows/MacOS/badge.svg)](https://github.com/lighttab2/qt-template/actions)
[![Actions Status](https://github.com/lighttab2/qt-template/workflows/Windows/badge.svg)](https://github.com/lighttab2/qt-template/actions)
[![Actions Status](https://github.com/lighttab2/qt-template/workflows/Ubuntu/badge.svg)](https://github.com/lighttab2/qt-template/actions)
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

### Install packages using *Conan*:

```bash
conan install conan/ --build=missing
```

### [Simply run *CMake*:](https://cmake.org/runningcmake/)

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

## Features
[List of features]

## Troubleshooting

<details><summary>Need to add a new library</summary>

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
conan install conan/ --build=missing
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

</details>

<details><summary>Qt is not found, despite being installed</summary>

Ensure that these **environment variables** are set properly:

* **Qt6_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6`<br/>example: `C:/Qt/6.5.1/msvc2019_64/lib/cmake/Qt6`

* **Qt6GuiTools_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6GuiTools`<br/>example: `/usr/lib/x86_64-linux-gnu/6.5.1/clang_64/lib/cmake/Qt6GuiTools`

* **Qt6CoreTools_DIR** - `[path_to_Qt]/[version]/[compiler]/lib/cmake/Qt6CoreTools`<br/>example: `D:/Qt/6.3/msvc2019_64/lib/cmake/Qt6CoreTools`
</details>

<details><summary>Missing or wrong libraries | Profile errors</summary>

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

</details>

<details><summary>Changing the name of the project</summary>

To change the name of the project, you must correct a few entries:
 
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

If the name contains *whitespace characters*, you will need to enclose the entire entry in either `"` or `'`. Example:

```yaml
files: build/install/${{ steps.repoName.outputs.name }}_macOS_${{ steps.versionTag.outputs.tag }}.tar.gz
```

Becomes:

```yaml
files: "build/install/Parrots and Cats_macOS_${{ steps.versionTag.outputs.tag }}.tar.gz"
```

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

</details>
</li>
</ul>
</details>

<details><summary>Changing the icon of the project</summary>

Put your **icon image** in **PNG** format into a folder `icon/` and **rename** it, so it matches this convention:

```ini
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

*macOS* icon is slightly tricky on *Windows*, as we do not have a ready script. I recommend using [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) or another form of virtualization (i.e.: [VirtualBox](https://www.virtualbox.org/) or [Docker](https://www.docker.com/)) and running the *Unix script* `/icon/UnixScripts/createIcns.sh`.\
If you are on *macOS*, you can do this the **native way**, using [iconutil](https://stackoverflow.com/questions/12306223/how-to-manually-create-icns-files-using-iconutil). Otherwise, run `/icon/UnixScripts/createIcns.sh`, which requires `png2icns` library. On *Ubuntu* you can install it by:

```bash
sudo apt install icnsutils
```
    
</details>

<details><summary>Docs shouldn't contain private members</summary>

If your project is a library, you might not want to add the private and protected members to your documentation. Editing one line in `.github/workflows/doxygen.yml` can change this behaviour. Find this step:

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


</details>

## Contributing

This project follows these [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), and it would be fun if you followed them too. If you don't, someone will correct your code. An ugly contribution is better than no contribution. **Thanks**!

## License

This project is licensed under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/); see the
[LICENSE](LICENSE) file for details.
It also uses the [Qt](https://www.qt.io/) library and possibly some of its additional modules that are licensed under the [LGPL](https://www.gnu.org/licenses/lgpl-3.0.en.html), but **none** of its code is present in this repository. Also note that *Qt* itself uses [other third-party libraries](https://doc.qt.io/qt-6/licenses-used-in-qt.html) under **different** license terms.
