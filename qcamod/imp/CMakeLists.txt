#compile QCADesigner code as a library named libqcamod
set(QCAMOD_SRC
        ${STDIO_FILEIO_FILES}
        ${PROJECT_SOURCE_DIR}/src/fileio_helpers.c
        ${PROJECT_SOURCE_DIR}/src/custom_widgets.c

        ${PROJECT_SOURCE_DIR}/src/simulation.c
        ${PROJECT_SOURCE_DIR}/src/simulation_data.c
        ${PROJECT_SOURCE_DIR}/src/bistable_simulation.c
        ${PROJECT_SOURCE_DIR}/src/coherence_vector.c
        ${PROJECT_SOURCE_DIR}/src/vector_table.c

        ${PROJECT_SOURCE_DIR}/src/design.c

        ${OBJECT_FILES}
        ${PROJECT_SOURCE_DIR}/src/objects/object_helpers.c

        ${PROJECT_SOURCE_DIR}/src/exp_array.c
        ${PROJECT_SOURCE_DIR}/src/hsl2rgb.c
        ${PROJECT_SOURCE_DIR}/src/generic_utils.c
        )
add_library(qcamod SHARED ${QCAMOD_SRC})
target_link_libraries(qcamod ${GTK2_LIBRARIES})
target_compile_options(qcamod PUBLIC -DSTDIO_FILEIO)

include_directories(${PROJECT_SOURCE_DIR}/qcamod/imp)

#swig files
SET_SOURCE_FILES_PROPERTIES(generate_qca_and_sim_from_structure.i PROPERTIES SWIG_FLAGS "-includeall")
SWIG_ADD_MODULE(generate_qca_and_sim_from_structure python generate_qca_and_sim_from_structure.i generate_qca_and_sim_from_structure.c)
SWIG_LINK_LIBRARIES(generate_qca_and_sim_from_structure ${PYTHON_LIBRARIES} ${GTK2_LIBRARIES} qcamod)

SET_SOURCE_FILES_PROPERTIES(generate_truth_from_sim.i PROPERTIES CPLUSPLUS ON)
SET_SOURCE_FILES_PROPERTIES(generate_truth_from_sim.i PROPERTIES SWIG_FLAGS "-includeall")
SWIG_ADD_MODULE(generate_truth_from_sim python generate_truth_from_sim.i generate_truth_from_sim.cpp)
SWIG_LINK_LIBRARIES(generate_truth_from_sim ${PYTHON_LIBRARIES} ${Boost_LIBRARIES})