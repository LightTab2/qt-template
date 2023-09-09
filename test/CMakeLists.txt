cmake_minimum_required(VERSION 3.21)

find_package(Qt6 REQUIRED COMPONENTS Test)

project(${CMAKE_PROJECT_NAME}Tests
        LANGUAGES CXX)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")

# Fix directories to be relative in qrc system
foreach(QML_FILE ${QML_FILES})
    file(RELATIVE_PATH QML_FILE_PATH ${CMAKE_SOURCE_DIR}/src ${QML_FILE})
    set_source_files_properties(${QML_FILE} PROPERTIES
                                QT_RESOURCE_ALIAS ${QML_FILE_PATH})
endforeach()

foreach(file ${TEST_FILES})
    string(REGEX REPLACE "(.*/)([a-zA-Z0-9_ ]+)(\.cpp)" "\\2" test_name ${file}) 

    # Create library/application, setup header and source files
    qt_add_executable(${test_name}_Tests ${file})
    target_compile_features(${test_name}_Tests PUBLIC cxx_std_${CMAKE_CXX_STANDARD})
    target_include_directories(${test_name}_Tests
                               PUBLIC
                               $<INSTALL_INTERFACE:include>
                               $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
                               ${CMAKE_INCLUDE_PATH} 
                               PRIVATE
                               ${CMAKE_SOURCE_DIR}/src
                               ${CMAKE_SOURCE_DIR}/src/qml)


    if (${CMAKE_PROJECT_NAME}_QT_QUICK)
        qt_add_qml_module(${test_name}_Tests
                          URI ${QML_URI}
                          RESOURCE_PREFIX "/qt/qml/"
                          QML_FILES ${QML_FILES}
                          RESOURCES ${TEST_RESOURCES}
                          NO_CACHEGEN
                          NO_PLUGIN)
    else()
        qt_add_resources(${test_name}_Tests "resources"
        PREFIX "/resource"
        FILES ${TEST_RESOURCES})
    endif()

    target_link_directories(${test_name}_Tests
                            PRIVATE
                            ${CMAKE_LIBRARY_PATH})

    target_link_libraries(${test_name}_Tests PRIVATE Qt6::Test)

    # Link libraries
    foreach(library IN LISTS MODULES)
        target_link_libraries(${test_name}_Tests PRIVATE ${library})
    endforeach()

    # Link Qt libraries
    foreach(library IN LISTS QT_COMPONENTS)
        target_link_libraries(${test_name}_Tests PRIVATE Qt6::${library})
    endforeach()

    foreach(library IN LISTS BOOST_COMPONENTS)
        target_link_libraries(${test_name}_Tests PRIVATE Boost::${library})
    endforeach()

    if(${CMAKE_PROJECT_NAME}_BUILD_EXECUTABLE)
        set(${CMAKE_PROJECT_NAME}_TEST_LIB ${CMAKE_PROJECT_NAME}_LIB)
    else()
        set(${CMAKE_PROJECT_NAME}_TEST_LIB ${CMAKE_PROJECT_NAME})
    endif()

    target_link_libraries(${test_name}_Tests PRIVATE ${${CMAKE_PROJECT_NAME}_TEST_LIB})

    add_test(NAME ${test_name}
             COMMAND ${test_name}_Tests)
endforeach()
