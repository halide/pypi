cmake_minimum_required(VERSION 3.21)
project(halide-llvm LANGUAGES C CXX)

# =============================================================================
# 1. Retrieve the Ref (Source of Truth)
# =============================================================================
set(HALIDE_LLVM_REF "$ENV{HALIDE_LLVM_REF}")
if (NOT HALIDE_LLVM_REF)
    message(FATAL_ERROR
        "HALIDE_LLVM_REF environment variable is required.\n"
        "Examples: 'llvmorg-21.1.8', 'main', or a commit SHA"
    )
endif ()

# =============================================================================
# 2. Calculate the Source Path
# =============================================================================
# Must match Python's sanitize_ref_for_path logic: replace invalid chars with _
string(REGEX REPLACE "[\\\\/:*?\"<>|]" "_" SAFE_REF "${HALIDE_LLVM_REF}")
set(LLVM_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src_cache/${SAFE_REF}")

# Validate that the source was downloaded by the version provider
if (NOT EXISTS "${LLVM_SOURCE_DIR}/llvm/CMakeLists.txt")
    message(FATAL_ERROR
        "LLVM source for ref '${HALIDE_LLVM_REF}' not found at:\n"
        "  ${LLVM_SOURCE_DIR}\n"
        "The Python version provider should have downloaded it.\n"
        "Try running: HALIDE_LLVM_REF=${HALIDE_LLVM_REF} pip wheel ."
    )
endif ()

message(STATUS "halide-llvm: Configuring LLVM from ${LLVM_SOURCE_DIR}")

# =============================================================================
# 3. Apply LLVM Configuration from Toolchain
# =============================================================================
# The toolchain file (via CMAKE_TOOLCHAIN_FILE) should have already included
# toolchains/initial-cache.cmake which sets all the LLVM_* variables.
#
# If no toolchain was specified, include the initial cache directly.
if (NOT CMAKE_TOOLCHAIN_FILE)
    message(STATUS "halide-llvm: No toolchain file specified, using initial-cache.cmake")
    include("${CMAKE_CURRENT_SOURCE_DIR}/toolchains/initial-cache.cmake")
endif ()

# =============================================================================
# 4. Locate zlib (provided by the halide-zlib wheel)
# =============================================================================
# LLVM is built with LLVM_ENABLE_ZLIB=FORCE_ON against our static halide-zlib
# package. Callers may pass -DZLIB_ROOT=... or set the ZLIB_ROOT environment
# variable explicitly (e.g. when cross-compiling x86-32-windows from a 64-bit
# Python environment); otherwise we locate the installed halide-zlib wheel via
# Python's importlib.metadata.
if (NOT ZLIB_ROOT AND NOT "$ENV{ZLIB_ROOT}" STREQUAL "")
    set(ZLIB_ROOT "$ENV{ZLIB_ROOT}")
endif ()

if (NOT ZLIB_ROOT)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    execute_process(
        COMMAND
            "${Python3_EXECUTABLE}"
            -c "from importlib.metadata import distribution; print(distribution('halide-zlib').locate_file('halide-zlib'))"
        OUTPUT_VARIABLE _halide_zlib_root
        OUTPUT_STRIP_TRAILING_WHITESPACE
        COMMAND_ERROR_IS_FATAL ANY
    )
    if (NOT IS_DIRECTORY "${_halide_zlib_root}")
        message(FATAL_ERROR "Could not locate halide-zlib prefix: ${_halide_zlib_root}")
    endif ()
    file(TO_CMAKE_PATH "${_halide_zlib_root}" ZLIB_ROOT)
    unset(_halide_zlib_root)
else ()
    file(TO_CMAKE_PATH "${ZLIB_ROOT}" ZLIB_ROOT)
endif ()

set(ZLIB_ROOT "${ZLIB_ROOT}" CACHE PATH "Root directory of halide-zlib" FORCE)
set(ZLIB_USE_STATIC_LIBS ON CACHE BOOL "Link against static zlib" FORCE)
message(STATUS "halide-llvm: Using ZLIB_ROOT=${ZLIB_ROOT}")

# =============================================================================
# 5. Build LLVM
# =============================================================================
add_subdirectory("${LLVM_SOURCE_DIR}/llvm" llvm-build)

# =============================================================================
# 6. Post-install fixup: point LLVMConfig.cmake at the sibling halide-zlib wheel
# =============================================================================
# LLVMConfig.cmake calls find_package(ZLIB) for the ZLIB::ZLIB target that
# LLVMSupport links to, after setting ZLIB_ROOT to the build-time value above.
# Rewrite it so installed wheels locate the sibling halide-zlib package in
# site-packages (while still honoring a caller-supplied ZLIB_ROOT).
install(CODE "set(HALIDE_LLVM_BUILD_ZLIB_ROOT \"${ZLIB_ROOT}\")")
install(CODE [[
    set(config "${CMAKE_INSTALL_PREFIX}/lib/cmake/llvm/LLVMConfig.cmake")
    file(READ "${config}" contents)
    set(baked_line "set(ZLIB_ROOT ${HALIDE_LLVM_BUILD_ZLIB_ROOT})")
    string(FIND "${contents}" "${baked_line}" at)
    if (at EQUAL -1)
        message(FATAL_ERROR "Did not find '${baked_line}' in ${config}")
    endif ()
    set(replacement [=[if(NOT ZLIB_ROOT)
    get_filename_component(_halide_zlib_root "${LLVM_INSTALL_PREFIX}/../../halide-zlib" ABSOLUTE)
    if(EXISTS "${_halide_zlib_root}")
      set(ZLIB_ROOT "${_halide_zlib_root}")
    endif()
    unset(_halide_zlib_root)
  endif()]=])
    string(REPLACE "${baked_line}" "${replacement}" contents "${contents}")
    file(WRITE "${config}" "${contents}")
]])

# =============================================================================
# 7. Post-install cleanup: convert clang symlinks to wrappers
# =============================================================================
# LLVM creates symlinks like clang++ -> clang, but wheels are ZIP files that
# don't support symlinks. Each "symlink" becomes a full ~128MB copy.
# We replace them with small bash wrappers to save space while keeping functionality.
install(CODE "set(CONVERT_SYMLINK_SCRIPT \"${CMAKE_CURRENT_SOURCE_DIR}/convert-symlink.sh\")")
install(CODE [[
    file(GLOB binaries "${CMAKE_INSTALL_PREFIX}/bin/*")
    foreach (binary IN LISTS binaries)
        if (IS_SYMLINK "${binary}")
            message(STATUS "Converting symlink: ${binary}")
            execute_process(
                COMMAND bash "${CONVERT_SYMLINK_SCRIPT}" "${binary}"
                RESULT_VARIABLE res
                ERROR_VARIABLE err
            )
            if (NOT res EQUAL 0)
                message(FATAL_ERROR "Failed to convert symlink: ${err}")
            endif ()
        endif ()
    endforeach ()
]])
