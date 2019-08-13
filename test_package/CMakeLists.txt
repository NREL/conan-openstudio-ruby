project(openstudio)
cmake_minimum_required(VERSION 3.10.2)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

#include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
#conan_basic_setup(TARGETS)

if(NOT CONAN_OPENSTUDIO_ALREADY_RUN)

  set(CMAKE_CONAN_EXPECTED_HASH 709180234748692a642f9e5c4d80d328)
  set(CMAKE_CONAN_VERSION "v0.14")

  if(EXISTS "${CMAKE_BINARY_DIR}/conan.cmake")
    file(MD5 "${CMAKE_BINARY_DIR}/conan.cmake" CMAKE_CONAN_HASH)
  endif()
  if(NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake" OR NOT "${CMAKE_CONAN_HASH}" MATCHES "${CMAKE_CONAN_EXPECTED_HASH}")
    # Put it in CMAKE_BINARY_DIR so we don't end up with two when building OpenStudioApplication
    message(STATUS "openstudio: Downloading conan.cmake ${CMAKE_CONAN_VERSION} from https://github.com/conan-io/cmake-conan")
    file(DOWNLOAD "https://github.com/conan-io/cmake-conan/raw/${CMAKE_CONAN_VERSION}/conan.cmake"
       "${CMAKE_BINARY_DIR}/conan.cmake")
  else()
    message(STATUS "openstudio: using existing conan.cmake")
  endif()

  include(${CMAKE_BINARY_DIR}/conan.cmake)

  conan_check(VERSION 1.0.0 REQUIRED)

  message(STATUS "openstudio: RUNNING CONAN")

  conan_add_remote(NAME bincrafters
    URL https://api.bintray.com/conan/bincrafters/public-conan)
  conan_add_remote(NAME nrel
    URL https://api.bintray.com/conan/commercialbuilding/nrel)

  list(APPEND CONAN_OPTIONS "zlib:minizip=True")
  # You do want to rebuild packages if there's a newer recipe in the remote (which applies mostly to our own openstudio_ruby where we don't
  # bump the actual package version when we make changes) than the binaries were built with
  # 'outdated' also acts like 'missing': if no binary, will build them.
  # list(APPEND CONAN_BUILD "outdated")


  # This will create the conanbuildinfo.cmake in the current binary dir, not the cmake_binary_dir
  conan_cmake_run(REQUIRES
    # Track NREL/stable in general, on a feature branch this could be temporarily switched to NREL/testing
    openstudio_ruby/2.5.5@nrel/stable
    BASIC_SETUP CMAKE_TARGETS NO_OUTPUT_DIRS
    OPTIONS ${CONAN_OPTIONS}
    BUILD ${CONAN_BUILD}
    # Passes `-u, --update`    to conan install: Check updates exist from upstream remotes
    # That and build=outdated should ensure we track the right
    # UPDATE
  )

  set(CONAN_OPENSTUDIO_ALREADY_RUN TRUE)

  #message("CONAN_TARGETS = ${CONAN_TARGETS}")
  message(STATUS "openstudio: DONE RUNNING CONAN")

else()

  message(STATUS "openstudio: CONAN RUN BY CALLING SCRIPT")

endif()

message("CONAN_LIBS=${CONAN_LIBS}")

set(MODULE_ROOT "${CONAN_OPENSTUDIO_RUBY_ROOT}")
if ("${MODULE_ROOT}" STREQUAL "")
  set(MODULE_ROOT "${CONAN_OPENSTUDIO_RUBY_ROOT_DEBUG}")
endif()

message("Searching for ruby modules in '${MODULE_ROOT}/lib/**/*.rb'")
file(GLOB_RECURSE  EXTENSION_RB  FOLLOW_SYMLINKS "${MODULE_ROOT}/lib/**/*.rb")

include_directories(${CMAKE_CURRENT_BINARY_DIR} ${PROJECT_BINARY_DIR} ${PROJECT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR} )

add_executable(${PROJECT_NAME}
  main.cpp
  # "${CMAKE_CURRENT_BINARY_DIR}/SWIGRubyRuntime.hxx"
  RubyException.hpp
  RubyInterpreter.hpp
  # "${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx"
  ${OUTPUT}
)

# We are setting up a set of artificial dependencies here so that
# cmake knows how to order the libraries properly
#
# Better: properly specifying these libs in the conan recipe
# At the moment this is not possible due to some of them coming from the OS and some
# being built by this project
# TODO: Continue to make the conan deps more robust and get this sorted out
add_library(additional_ruby_libs empty.cpp)

add_library(ruby_libs empty.cpp)
target_link_libraries(ruby_libs PUBLIC CONAN_PKG::openstudio_ruby)
target_link_libraries(ruby_libs PUBLIC additional_ruby_libs)


target_link_libraries(openstudio ruby_libs)

if (UNIX AND NOT APPLE)
  target_link_libraries(additional_ruby_libs dl crypt)
  target_link_libraries(openstudio "icui18n" "icuuc" "gmp")
elseif(WIN32)
  target_link_libraries(openstudio wsock32 ws2_32 Dbghelp Shlwapi)
  set_target_properties(openstudio PROPERTIES LINK_FLAGS_DEBUG "/NODEFAULTLIB:MSVCRT")
else()
endif()

if( APPLE )
  target_link_libraries(openstudio ${COREFOUNDATION_LIBRARY})
endif()
