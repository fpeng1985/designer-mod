#compile QCADesigner code as a library named libqcamod
set(QCAMOD_SRC
        ${STDIO_FILEIO_FILES}
        ../src/fileio_helpers.c
        ../src/custom_widgets.c

        ../src/simulation.c
        ../src/simulation_data.c
        ../src/bistable_simulation.c
        ../src/coherence_vector.c
        ../src/vector_table.c

        ../src/design.c

        ${OBJECT_FILES}
        ../src/objects/object_helpers.c

        ../src/exp_array.c
        ../src/hsl2rgb.c
        ../src/generic_utils.c
        )
add_library(qcamod SHARED ${QCAMOD_SRC})
target_link_libraries(qcamod ${GTK2_LIBRARIES})
target_compile_options(qcamod PUBLIC -DSTDIO_FILEIO)

#swig files
SET_SOURCE_FILES_PROPERTIES(generate_qca_and_sim_from_structure.i PROPERTIES SWIG_FLAGS "-includeall")
SWIG_ADD_MODULE(generate_qca_and_sim_from_structure python generate_qca_and_sim_from_structure.i generate_qca_and_sim_from_structure.c)
SWIG_LINK_LIBRARIES(generate_qca_and_sim_from_structure ${PYTHON_LIBRARIES} ${GTK2_LIBRARIES} qcamod)

SET_SOURCE_FILES_PROPERTIES(generate_truth_from_sim.i PROPERTIES CPLUSPLUS ON)
SET_SOURCE_FILES_PROPERTIES(generate_truth_from_sim.i PROPERTIES SWIG_FLAGS "-includeall")
SWIG_ADD_MODULE(generate_truth_from_sim python generate_truth_from_sim.i generate_truth_from_sim.cpp)
SWIG_LINK_LIBRARIES(generate_truth_from_sim ${PYTHON_LIBRARIES} ${Boost_LIBRARIES})

#independent tools
#add_executable(gen_qca_and_sim gen_qca_and_sim_tool.c generate_qca_and_sim_from_structure.c)
#target_link_libraries(gen_qca_and_sim ${GTK2_LIBRARIES} qcamod)
#
#add_executable(gen_truth gen_truth_tool.cpp generate_truth_from_sim.cpp)
#target_link_libraries(gen_truth ${Boost_LIBRARIES})

#python scripts
set(PY_SCRIPTS
        ${CMAKE_CURRENT_SOURCE_DIR}/main.py
        ${CMAKE_CURRENT_SOURCE_DIR}/qm.py
        )
add_custom_command(OUTPUT copy_python_scripts COMMAND ${CMAKE_COMMAND} -E copy ${PY_SCRIPTS} ${EXECUTABLE_OUTPUT_PATH})
add_custom_target(main_py ALL DEPENDS copy_python_scripts)