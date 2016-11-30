add_executable(qcamod
        ${STDIO_FILEIO_FILES}
        ../fileio_helpers.c
        ../custom_widgets.c

        ../simulation.c
        ../simulation_data.c
        ../bistable_simulation.c
        ../coherence_vector.c
        ../Vector_table.c

        ../design.c

        ${OBJECT_FILES}
        ../objects/object_helpers.c              ../objects/object_helpers.h

        ../exp_array.c
        ../hsl2rgb.c
        ../generic_utils.c

        qcamod.c
        )
target_link_libraries(qcamod m glib-2.0 intl gobject-2.0)
target_compile_options(qcamod PUBLIC -DSTDIO_FILEIO)

find_package(Boost COMPONENTS system filesystem program_options REQUIRED)
if(Boost_FOUND)
    include_directories(SYSTEM ${Boost_INCLUDE_DIRS})
    message(STATUS "Boost LIB : ${Boost_LIBRARIES}")
else(Boost_FOUND)
    message("Boost not found!")
endif(Boost_FOUND)

add_executable(sim_parser sim_parser.cpp)
target_link_libraries(sim_parser ${Boost_LIBRARIES})