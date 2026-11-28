cmake_minimum_required(VERSION 3.28)
project(halide-zlib LANGUAGES C)

set(CMAKE_POSITION_INDEPENDENT_CODE ON CACHE BOOL "" FORCE)
set(CMAKE_INSTALL_LIBDIR "lib" CACHE STRING "" FORCE)

set(ZLIB_BUILD_SHARED OFF CACHE BOOL "" FORCE)
set(ZLIB_BUILD_STATIC ON CACHE BOOL "" FORCE)
set(ZLIB_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(ZLIB_INSTALL OFF CACHE BOOL "" FORCE)

add_subdirectory(repo)

# On Windows, zlib 1.3.2 names the static library `zs.lib`, which CMake's
# FindZLIB module only searches when ZLIB_USE_STATIC_LIBS is ON. Naming it
# `zlibstatic` ensures find_package(ZLIB) finds it regardless of whether
# ZLIB_USE_STATIC_LIBS is set (e.g. from LLVMConfig.cmake).
if (WIN32)
    set_target_properties(zlibstatic PROPERTIES OUTPUT_NAME zlibstatic)
endif ()

install(
    TARGETS zlibstatic
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(
    FILES
        "${CMAKE_CURRENT_BINARY_DIR}/repo/zconf.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/repo/zlib.h"
    DESTINATION include
)
install(
    FILES "${CMAKE_CURRENT_SOURCE_DIR}/repo/LICENSE"
    DESTINATION share/doc/zlib
)
