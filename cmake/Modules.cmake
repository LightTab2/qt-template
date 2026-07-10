set(SYS_MODULES)

set(MODULES)

set(BOOST_COMPONENTS filesystem)

set(QT_COMPONENTS Core Gui Widgets)

# Link the shared dependency set (MODULES, Qt components, Boost components,
# Microsoft.GSL) into the given target. Single source of truth for all targets.
function(project_link_dependencies target)
    foreach(library IN LISTS MODULES)
        target_link_libraries(${target} PRIVATE ${library})
    endforeach()
    foreach(library IN LISTS QT_COMPONENTS)
        target_link_libraries(${target} PRIVATE Qt6::${library})
    endforeach()
    foreach(library IN LISTS BOOST_COMPONENTS)
        target_link_libraries(${target} PRIVATE Boost::${library})
    endforeach()
    target_link_libraries(${target} PRIVATE Microsoft.GSL::GSL)
endfunction()
