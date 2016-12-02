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

SET_SOURCE_FILES_PROPERTIES(generate_truth_from_sim.i PROPERTIES CPLUSPLUS ON)
SET_SOURCE_FILES_PROPERTIES(generate_truth_from_sim.i PROPERTIES SWIG_FLAGS "-includeall")
SWIG_ADD_MODULE(generate_truth_from_sim python generate_truth_from_sim.i generate_truth_from_sim.cpp)
SWIG_LINK_LIBRARIES(generate_truth_from_sim ${PYTHON_LIBRARIES} ${Boost_LIBRARIES})

add_executable(sim_parser sim_parser_main.cpp generate_truth_from_sim.cpp)
target_link_libraries(sim_parser ${Boost_LIBRARIES})

set(PY_SCRIPTS
        ${CMAKE_CURRENT_SOURCE_DIR}/main.py
        ${CMAKE_CURRENT_SOURCE_DIR}/generate_simulation_files.py
        ${CMAKE_CURRENT_SOURCE_DIR}/generate_logic_files.py
        )
add_custom_command(OUTPUT _copy_python_scripts COMMAND ${CMAKE_COMMAND} -E copy ${PY_SCRIPTS} ${EXECUTABLE_OUTPUT_PATH})
add_custom_target(copy_python_scripts ALL DEPENDS _copy_python_scripts)