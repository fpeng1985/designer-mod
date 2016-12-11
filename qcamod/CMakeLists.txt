
#swig files
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

add_subdirectory(imp)