# Minimal CMake toolchain file forwarded to LLVM's bootstrapping runtimes
# sub-build (via RUNTIMES_CMAKE_ARGS).
#
# CMake >= 3.28 (CMP0155=NEW, enabled since LLVM 24 raised
# cmake_minimum_required to 3.31) scans C++20+ sources (libcxx/libcxxabi are
# compiled with -std=c++23) using clang-scan-deps, which initial-cache.cmake
# disables to keep wheel sizes down.
#
# Passing this via CMAKE_TOOLCHAIN_FILE instead of a plain -D variable ensures
# it also propagates into compiler-rt's nested add_custom_libcxx() sub-builds
# (such as libcxx_fuzzer_<arch> on Linux), whose PASSTHROUGH_VARIABLES list
# forwards CMAKE_TOOLCHAIN_FILE but not CMAKE_CXX_SCAN_FOR_MODULES.
#
# Intentionally does NOT set CMAKE_SYSTEM_NAME so CMAKE_CROSSCOMPILING stays
# FALSE.
set(CMAKE_CXX_SCAN_FOR_MODULES OFF CACHE BOOL "")
