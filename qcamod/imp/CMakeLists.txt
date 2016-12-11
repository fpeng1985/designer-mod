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
target_link_libraries(qcamod ${GTK3_LIBRARIES})
target_compile_options(qcamod PUBLIC -DSTDIO_FILEIO)

add_executable(generate_qca_and_sim_from_structure generate_qca_and_sim_from_structure.c
        generate_qca_and_sim_from_structure_imp.c)
target_link_libraries(generate_qca_and_sim_from_structure ${GTK3_LIBRARIES} qcamod)

include_directories(${PROJECT_SOURCE_DIR}/qcamod/imp)

#swig files
SET_SOURCE_FILES_PROPERTIES(generate_qca_and_sim_from_structure_imp.i PROPERTIES SWIG_FLAGS "-includeall")
SWIG_ADD_MODULE(generate_qca_and_sim_from_structure_imp python generate_qca_and_sim_from_structure_imp.i generate_qca_and_sim_from_structure_imp.c)
SWIG_LINK_LIBRARIES(generate_qca_and_sim_from_structure_imp ${PYTHON_LIBRARIES} ${GTK3_LIBRARIES} qcamod)