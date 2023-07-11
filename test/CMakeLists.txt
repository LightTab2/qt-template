cmake_minimum_required(VERSION 3.16)

find_package(Qt6 REQUIRED COMPONENTS Test)

project(${CMAKE_PROJECT_NAME}Tests
        LANGUAGES CXX)

foreach(file ${test_sources})
    string(REGEX REPLACE "(.*/)([a-zA-Z0-9_ ]+)(\.cpp)" "\\2" test_name ${file}) 
    qt_add_executable(${test_name}_Tests ${file})
    target_link_libraries(${test_name}_Tests PRIVATE Qt6::Test Qt6::Widgets)

    # Set the compiler standard

    target_compile_features(${test_name}_Tests PUBLIC cxx_std_17)

    # Setup code coverage if enabled

    if (${CMAKE_PROJECT_NAME}_ENABLE_CODE_COVERAGE)
        target_compile_options(${CMAKE_PROJECT_NAME} PUBLIC -O0 -g -fprofile-arcs -ftest-coverage)
        target_link_options(${CMAKE_PROJECT_NAME} PUBLIC -fprofile-arcs -ftest-coverage)
    endif()

    if(${CMAKE_PROJECT_NAME}_BUILD_EXECUTABLE)
        set(${CMAKE_PROJECT_NAME}_TEST_LIB ${CMAKE_PROJECT_NAME}_LIB)
    else()
        set(${CMAKE_PROJECT_NAME}_TEST_LIB ${CMAKE_PROJECT_NAME})
    endif()

    add_test(NAME ${test_name}
             COMMAND ${test_name}_Tests)
endforeach()
