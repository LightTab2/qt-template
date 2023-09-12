file(GLOB_RECURSE QML_FILES
     src/qml/*.qml)

# Fix directories to be relative in qrc system
foreach(QML_FILE ${QML_FILES})
    file(RELATIVE_PATH QML_FILE_PATH ${CMAKE_SOURCE_DIR}/src/qml ${QML_FILE})
    set_source_files_properties(${QML_FILE} PROPERTIES
                                QT_RESOURCE_ALIAS ${QML_FILE_PATH})
endforeach()

set(RESOURCES icon/icon_32x32.png)

# Prepend "../" to each path
foreach(Resource ${RESOURCES})
    string(CONCAT TestResource "../" ${Resource})
    list(APPEND TEST_RESOURCES ${TestResource})
endforeach()
