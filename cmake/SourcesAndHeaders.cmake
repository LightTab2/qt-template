file(GLOB SOURCE_FILES
     src/*.cpp
     src/*.h
     src/*.ui)

file(GLOB HEADER_FILES
     include/*.h)

file(GLOB TEST_FILES 
     test/*.cpp)

set(sources ${SOURCE_FILES})

set(headers ${HEADER_FILES})

set(test_sources ${TEST_FILES})
