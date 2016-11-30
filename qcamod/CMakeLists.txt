add_executable(qcamod
        ${STDIO_FILEIO_FILES}
        ../src/fileio_helpers.c
        ../src/custom_widgets.c

        ../src/simulation.c
        ../src/simulation_data.c
        ../src/bistable_simulation.c
        ../src/coherence_vector.c
        ../src/Vector_table.c

        ../src/design.c

        ${OBJECT_FILES}
        ../src/objects/object_helpers.c              ../src/objects/object_helpers.h

        ../src/exp_array.c
        ../src/hsl2rgb.c
        ../src/generic_utils.c

        qcamod.c
        )
target_link_libraries(qcamod m glib-2.0 intl gobject-2.0)
target_compile_options(qcamod PUBLIC -DSTDIO_FILEIO)

add_executable(sim_parser sim_parser.cpp)
target_link_libraries(sim_parser ${Boost_LIBRARIES})