#python scripts
set(PY_SCRIPTS
        ${CMAKE_CURRENT_SOURCE_DIR}/app.py
        ${CMAKE_CURRENT_SOURCE_DIR}/models.py
        ${CMAKE_CURRENT_SOURCE_DIR}/main.py
        ${CMAKE_CURRENT_SOURCE_DIR}/qm.py
        )

add_custom_command(OUTPUT copy_python_scripts COMMAND ${CMAKE_COMMAND} -E copy ${PY_SCRIPTS} ${EXECUTABLE_OUTPUT_PATH})
add_custom_target(copy_py ALL DEPENDS copy_python_scripts)


add_subdirectory(imp)