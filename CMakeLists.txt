cmake_minimum_required (VERSION 3.5.1)
project (qcadesigner-mod)

if( CMAKE_SYSTEM_NAME STREQUAL "Windows")
    add_definitions(-DWin32)
endif()

find_package (PkgConfig REQUIRED)
pkg_check_modules (GTK2 REQUIRED gtk+-2.0)

include_directories(${GTK2_INCLUDE_DIRS})
link_directories(${GTK2_LIBRARY_DIRS} C:/msys64/mingw64/x86_64-w64-mingw32/lib)

set(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)
set(LIBRARY_OUTPUT_PATH    ${PROJECT_BINARY_DIR}/lib)

set(CMAKE_C_COMPILER c:/msys64/mingw64/bin/gcc)
set(CMAKE_C_FLAGS "-mms-bitfields -pthread")

add_subdirectory(src)