cmake_minimum_required (VERSION 3.5.1)
project (designer-mod)

#platform specific settings
if( CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(CMAKE_C_COMPILER   c:/msys64/mingw64/bin/gcc)
    set(CMAKE_CXX_COMPILER c:/msys64/mingw64/bin/g++)
    link_directories(C:/msys64/mingw64/bin C:/msys64/mingw64/lib)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(BOOST_LIBRARYDIR /usr/lib/x86_64-linux-gnu)
endif()

#gtk2
find_package(PkgConfig REQUIRED)
pkg_check_modules(GTK2 REQUIRED gtk+-2.0)
include_directories(${GTK2_INCLUDE_DIRS})
link_directories(${GTK2_LIBRARY_DIRS})

#boost
find_package(Boost) #COMPONENTS system REQUIRED)
if(Boost_FOUND)
    include_directories(SYSTEM ${Boost_INCLUDE_DIRS})
else(Boost_FOUND)
    message("Boost not found!")
endif(Boost_FOUND)

#swig
find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

#python
find_package(PythonLibs 3 REQUIRED)
include_directories(${PYTHON_INCLUDE_PATH})

#set paths
set(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)
set(LIBRARY_OUTPUT_PATH    ${PROJECT_BINARY_DIR}/bin)
link_directories(${LIBRARY_OUTPUT_PATH})
set(CMAKE_SWIG_OUTDIR      ${PROJECT_BINARY_DIR}/bin)

#set compiler flags
set(CMAKE_C_FLAGS "-mms-bitfields -pthread")
set(CMAKE_CXX_FLAGS         "$ENV{CXXFLAGS} -Wall -std=c++14")
set(CMAKE_CXX_FLAGS_DEBUG   "${CMAKE_CXX_FLAGS} -O0 -g -ggdb")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS} -O3 -DNDEBUG -msse2")

#program specific settings
set(UNDO_REDO_FILES
        ${PROJECT_SOURCE_DIR}/src/objects/QCADUndoEntry.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADUndoEntry.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADUndoEntryGroup.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADUndoEntryGroup.h
        ${PROJECT_SOURCE_DIR}/src/selection_undo.c
        ${PROJECT_SOURCE_DIR}/src/selection_undo.h
        )

set(STDIO_FILEIO_FILES
        ${PROJECT_SOURCE_DIR}/src/fileio.c
        ${PROJECT_SOURCE_DIR}/src/fileio.h
        )

set(OBJECT_FILES
        ${PROJECT_SOURCE_DIR}/src/objects/QCADCell.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADCell.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADCompoundDO.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADCompoundDO.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADDesignObject.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADDesignObject.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADDOContainer.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADDOContainer.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADLabel.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADLabel.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADLayer.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADLayer.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADRuler.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADRuler.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADStretchyObject.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADStretchyObject.h
        ${PROJECT_SOURCE_DIR}/src/objects/QCADSubstrate.c
        ${PROJECT_SOURCE_DIR}/src/objects/QCADSubstrate.h
        )

#sub dirs
add_subdirectory(src)
add_subdirectory(qcamod)