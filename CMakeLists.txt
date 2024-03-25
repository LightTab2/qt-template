cmake_minimum_required(VERSION 3.21)

project("qt-template"
        LANGUAGES CXX)

# Find all needed libraries
include(cmake/Modules.cmake)
foreach(library IN LISTS MODULES)
    find_package(${library} REQUIRED)
endforeach()

foreach(library IN LISTS QT_COMPONENTS)
    find_package(Qt6 COMPONENTS ${library} REQUIRED)
    string(TOLOWER "${library}" library_lower)
    if (library_lower STREQUAL "quick")
        set(${PROJECT_NAME}_QT_QUICK ON)
    endif()
endforeach()

set(Boost_USE_STATIC_LIBS OFF) 
set(Boost_USE_MULTITHREADED ON)  
set(Boost_USE_STATIC_RUNTIME OFF) 
foreach(library IN LISTS BOOST_COMPONENTS)
    find_package(Boost COMPONENTS ${library} REQUIRED)
endforeach()

# Setup
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)

qt_standard_project_setup()

# Model project dependencies
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")

include(cmake/StandardSettings.cmake)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
endif()

if (UNIX)
    add_compile_options("$<$<CONFIG:DEBUG>:-D_DEBUG>")    #this will allow to use same _DEBUG macro available in both Unix as well as Windows - MSCV environment. Easy to put Debug specific code
endif (UNIX)

# Setup alternative names
if(${PROJECT_NAME}_USE_ALT_NAMES)
    string(TOLOWER ${PROJECT_NAME} PROJECT_NAME_LOWERCASE)
    string(TOUPPER ${PROJECT_NAME} PROJECT_NAME_UPPERCASE)
else()
    set(PROJECT_NAME_LOWERCASE ${PROJECT_NAME})
    set(PROJECT_NAME_UPPERCASE ${PROJECT_NAME})
endif()

# Prevent building in the source directory
if(PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
  message(FATAL_ERROR "In-source builds not allowed. Please make a new directory (called a build directory) and run CMake from there.\n")
endif()

# Find all headers and implementation files
include(cmake/Sources.cmake)

# Create library/application, setup header and source files
if(${PROJECT_NAME}_BUILD_EXECUTABLE)
    if (APPLE)
        # Check for icon
        if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.icns")
            qt_add_executable(${PROJECT_NAME} MACOSX_BUNDLE ${SOURCE_FILES} "${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.icns")
        else()
            qt_add_executable(${PROJECT_NAME} MACOSX_BUNDLE ${SOURCE_FILES})
        endif()
    elseif(WIN32)
        # Check for icon
        if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.rc" AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.ico")
            qt_add_executable(${PROJECT_NAME} WIN32 ${SOURCE_FILES} "${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.rc")
        else()
            qt_add_executable(${PROJECT_NAME} WIN32 ${SOURCE_FILES})
        endif()
    else()
        # Icons added at deployment
        qt_add_executable(${PROJECT_NAME} ${SOURCE_FILES})
    endif()
    target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_${CMAKE_CXX_STANDARD})
    qt_add_library(${PROJECT_NAME}_LIB STATIC ${SOURCE_FILES})
    set_target_properties(${PROJECT_NAME}_LIB
                          PROPERTIES
                          ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib/${CMAKE_BUILD_TYPE}"
                          LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib/${CMAKE_BUILD_TYPE}"
                          OUTPUT_NAME ${PROJECT_NAME})
    target_compile_features(${PROJECT_NAME}_LIB PUBLIC cxx_std_${CMAKE_CXX_STANDARD})
else()
    qt_add_library(${PROJECT_NAME} STATIC ${SOURCE_FILES})
    target_compile_features(${PROJECT_NAME} PUBLIC cxx_std_${CMAKE_CXX_STANDARD})
endif()

if (NOT ${PROJECT_NAME}_BUILD_EXECUTABLE)
    set_target_properties(${PROJECT_NAME}
                          PROPERTIES
                          ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib/${CMAKE_BUILD_TYPE}"
                          LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib/${CMAKE_BUILD_TYPE}"
                          RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/${CMAKE_BUILD_TYPE}")
endif()

# Set the project standard and warnings
include(cmake/CompilerWarnings.cmake)
set_project_warnings(${PROJECT_NAME})

# Allow usage of header files in the `src` directory, but only for utilities
target_include_directories(${PROJECT_NAME}
                           PUBLIC
                           $<INSTALL_INTERFACE:include>
                           $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
                           ${CMAKE_INCLUDE_PATH} 
                           PRIVATE
                           ${CMAKE_CURRENT_SOURCE_DIR}/src
                           ${CMAKE_CURRENT_SOURCE_DIR}/src/qml)
target_link_directories(${PROJECT_NAME}
                        PRIVATE
                        ${CMAKE_LIBRARY_PATH})

if(${PROJECT_NAME}_BUILD_EXECUTABLE)
    target_include_directories(${PROJECT_NAME}_LIB
                               PUBLIC
                               $<INSTALL_INTERFACE:include>
                               $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
                               ${CMAKE_INCLUDE_PATH} 
                               ${CMAKE_CURRENT_SOURCE_DIR}/src
                               ${CMAKE_CURRENT_SOURCE_DIR}/src/qml)
    target_link_directories(${PROJECT_NAME}_LIB
                            PRIVATE
                            ${CMAKE_LIBRARY_PATH})
endif()

# Link libraries
foreach(library IN LISTS MODULES)
    target_link_libraries(${PROJECT_NAME} PRIVATE ${library})
    if(${PROJECT_NAME}_BUILD_EXECUTABLE)
        target_link_libraries(${PROJECT_NAME}_LIB PRIVATE ${library})
    endif()
endforeach()

# Link Qt libraries
foreach(library IN LISTS QT_COMPONENTS)
    target_link_libraries(${PROJECT_NAME} PRIVATE Qt6::${library})
    if(${PROJECT_NAME}_BUILD_EXECUTABLE)
        target_link_libraries(${PROJECT_NAME}_LIB PRIVATE Qt6::${library})
    endif()
endforeach()

foreach(library IN LISTS BOOST_COMPONENTS)
    target_link_libraries(${PROJECT_NAME} PRIVATE Boost::${library})
    if(${PROJECT_NAME}_BUILD_EXECUTABLE)
        target_link_libraries(${PROJECT_NAME}_LIB PRIVATE Boost::${library})
    endif()
endforeach()

# Create code filters
 # For source code
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.h" "src/*.ui")
foreach(SOURCE ${SOURCES})
    get_filename_component(SOURCE_DIR "${SOURCE}" DIRECTORY)
    file(RELATIVE_PATH SOURCE_PATH "${CMAKE_CURRENT_SOURCE_DIR}" ${SOURCE_DIR})
    string(REPLACE "src" "Source Files" SOURCE_PATH "${SOURCE_PATH}")
    source_group("${SOURCE_PATH}" FILES ${SOURCE})
endforeach()
 # For resources
file(GLOB_RECURSE SOURCES "*.rc" "*.qrc")
foreach(SOURCE ${SOURCES})
    source_group("Resources" FILES ${SOURCE})
endforeach()
source_group("Resources" FILES 
             "${CMAKE_BINARY_DIR}/.rcc/resources.qrc"
             "${CMAKE_BINARY_DIR}/.rcc/qrc_resources.cpp")

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

# Resources
include(cmake/Resources.cmake)
string(REPLACE "-" "_" QML_URI "${PROJECT_NAME}")
if (${PROJECT_NAME}_QT_QUICK)
    qt_add_qml_module(${PROJECT_NAME}
                      URI ${QML_URI} 
                      RESOURCE_PREFIX "/qt/qml/"
                      QML_FILES ${QML_FILES}
                      RESOURCES ${RESOURCES}
                      NO_PLUGIN)
else()
    qt_add_resources(${PROJECT_NAME} "resources"
    PREFIX "/resource"
    FILES ${RESOURCES})
endif()

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

# Provide alias to library for
if(${PROJECT_NAME}_BUILD_EXECUTABLE)
    add_executable(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})
else()
    add_library(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})
endif()

# Deployment
if(APPLE)
    set_target_properties(${PROJECT_NAME} PROPERTIES
                          MACOSX_BUNDLE TRUE)
    if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.icns")
        set(MACOSX_BUNDLE_ICON_FILE icon.icns)
        set_source_files_properties("${CMAKE_CURRENT_SOURCE_DIR}/icon/icon.icns" PROPERTIES
                                    MACOSX_PACKAGE_LOCATION "Resources")
    endif()
elseif(WIN32)
    set_target_properties(${PROJECT_NAME} PROPERTIES
                          WIN32_EXECUTABLE TRUE)
endif()

# Install target
if(APPLE)
    install(TARGETS ${PROJECT_NAME}
            CONFIGURATIONS Release
            BUNDLE DESTINATION .)
    set(EXECUTABLE_PATH "./$<TARGET_FILE_NAME:${PROJECT_NAME}>.app")
    set(CMAKE_INSTALL_PREFIX "./install")
else()
    install(TARGETS ${PROJECT_NAME}
            CONFIGURATIONS Release
            RUNTIME DESTINATION .)
    if(UNIX)
        set(CMAKE_INSTALL_PREFIX "$ENV{HOME}/install")
    else()
        set(CMAKE_INSTALL_PREFIX "install")
    endif()
    set(EXECUTABLE_PATH "$<TARGET_FILE:${PROJECT_NAME}>")
endif()

qt_generate_deploy_script(TARGET ${PROJECT_NAME}
                          OUTPUT_SCRIPT DEPLOY_SCRIPT
                          CONTENT "
                          qt_deploy_runtime_dependencies(EXECUTABLE \"${EXECUTABLE_PATH}\"
                          BIN_DIR .
                          VERBOSE)")

install(SCRIPT ${DEPLOY_SCRIPT})

# Unit testing setup
enable_testing(true)
add_subdirectory(test)
