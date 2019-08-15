cmake_minimum_required(VERSION 3.10.2)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_VERBOSE_MAKEFILE TRUE)


# Use ccache is available, has to be before "project()"
find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
  # Support Unix Makefiles and Ninja
  set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CCACHE_PROGRAM}")
endif()

project(openstudio)

# Xcode/Ninja generators undefined MAKE
if(CMAKE_GENERATOR MATCHES "Make")
  set(MAKE "$(MAKE)")
else()
  set(MAKE make)
endif()

# Add Color Output if Using Ninja
macro(AddCXXFlagIfSupported flag test)
  CHECK_CXX_COMPILER_FLAG(${flag} ${test})
  if(${${test}})
    message("adding ${flag}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${flag}")
  endif()
endmacro()

if("Ninja" STREQUAL ${CMAKE_GENERATOR})
  # Clang
  if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
    AddCXXFlagIfSupported(-fcolor-diagnostics COMPILER_SUPPORTS_fcolor-diagnostics)
  endif()

  # g++
  if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    # For some reason it doesn't say its supported, but it works...
    # AddCXXFlagIfSupported(-fdiagnostics-color COMPILER_SUPPORTS_fdiagnostics-color)
    message(STATUS "Ninja: Forcing -fdiagnostics-color=always")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fdiagnostics-color=always")
  endif()
endif()

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

message("CONAN_LIBS=${CONAN_LIBS}")

set(MODULE_ROOT "${CONAN_OPENSTUDIO_RUBY_ROOT}")
if ("${MODULE_ROOT}" STREQUAL "")
  set(MODULE_ROOT "${CONAN_OPENSTUDIO_RUBY_ROOT_DEBUG}")
endif()


#######################################################################
#                               S W I G                               #
#######################################################################

# We use conan swig_installer which enhances our PATH to include the CONAN_BIN_DIRS_SWIG_INSTALLER already
# So I could just do:
# set(SWIG_EXECUTABLE swig)
# But better be safe
find_program(SWIG_EXECUTABLE swig)
if(NOT SWIG_EXECUTABLE)
  message(FATAL_ERROR "Couldn't find swig, which shouldn't happen. CONAN_BIN_DIRS_SWIG_INSTALLER=${CONAN_BIN_DIRS_SWIG_INSTALLER}")
endif()

#######################################################################
#                        E M B E D   F I L E S                        #
#######################################################################

# TODO: WE DO NEED TO EMBED STUFF, SO PUT THAT BACK!
include("embedded/EmbedFiles.cmake")
add_subdirectory("embedded")

message("Searching for ruby modules in '${MODULE_ROOT}/lib/**/*.rb'")
file(GLOB_RECURSE  EXTENSION_RB  FOLLOW_SYMLINKS "${MODULE_ROOT}/lib/**/*.rb")

foreach( _FILE ${EXTENSION_RB} )
  file(RELATIVE_PATH LOCATION ${MODULE_ROOT}/lib ${_FILE})
  list(APPEND FILES ${_FILE})
  list(APPEND EMBEDDED_PATHS ${LOCATION})
endforeach()

list(APPEND FILES "${CMAKE_CURRENT_SOURCE_DIR}/embedded_help.rb")
list(APPEND EMBEDDED_PATHS "embedded_help.rb")

list(APPEND FILES "${CMAKE_CURRENT_SOURCE_DIR}/openstudio_cli.rb")
list(APPEND EMBEDDED_PATHS "openstudio_cli.rb")

embed_files("${FILES}" "${EMBEDDED_PATHS}" OUTPUT)

set_source_files_properties(EmbeddedScripting.i
  PROPERTIES CPLUSPLUS true
)

include_directories(${CMAKE_CURRENT_BINARY_DIR} ${PROJECT_BINARY_DIR} ${PROJECT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR} )

add_custom_command(
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/SWIGRubyRuntime.hxx"
  COMMAND "${SWIG_EXECUTABLE}"
          "-ruby"
          -external-runtime "${CMAKE_CURRENT_BINARY_DIR}/SWIGRubyRuntime.hxx"
)

add_custom_command(
  OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx"
  COMMAND "${SWIG_EXECUTABLE}"
          "-ruby"
          "-c++"
          -o "${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx"
          "-fvirtual"
          "-I${PROJECT_SOURCE_DIR}/src"
          "-I${PROJECT_BINARY_DIR}/src"
          "-D_WINDOWS"
          "-Fmicrosoft"
          "${CMAKE_CURRENT_SOURCE_DIR}/EmbeddedScripting.i"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/EmbeddedScripting.i"
          "${CMAKE_CURRENT_BINARY_DIR}/embedded_files.hxx"
          "EmbeddedHelp.hpp"
)

set_source_files_properties(${EMBED_SOURCE_FILES} PROPERTIES HEADER_FILE_ONLY TRUE)

source_group(embedded_files FILES ${OUTPUT})

add_executable(${PROJECT_NAME}
  main.cpp
  "${CMAKE_CURRENT_BINARY_DIR}/SWIGRubyRuntime.hxx"
  RubyException.hpp
  RubyInterpreter.hpp
  "${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx"
  ${OUTPUT}
)

# -Wno-deprecated-declaration, /wd4996: suppresses deprecated warning
# -Wno-register, /wd5033: ISO C++1z does not allow *register* storage class specifier
if(MSVC)
  set_target_properties(${PROJECT_NAME} PROPERTIES COMPILE_FLAGS "/bigobj /wd4996 /wd5033")
  set_source_files_properties("${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx" PROPERTIES COMPILE_FLAGS "-DRUBY_EMBEDDED" )
else()
  set_target_properties(${PROJECT_NAME} PROPERTIES COMPILE_FLAGS "-Wno-deprecated-declarations -Wno-register")
  set_source_files_properties("${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx" PROPERTIES COMPILE_FLAGS "-DRUBY_EMBEDDED -Wno-unused-variable" )
endif()

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

if(WIN32)
  # link target with debug and release libs
  function(LINK_DEBUG_AND_RELEASE this_target debug_libs release_libs)
    list(LENGTH debug_libs len1)
    list(LENGTH release_libs len2)

    if (NOT len1 EQUAL len2)
      message(SEND_ERROR "Unequal lists passed to LINK_DEBUG_AND_RELEASE")
    endif()

    math(EXPR len "${len1} - 1")

    foreach(i RANGE ${len})
      list(GET debug_libs ${i} debug_lib)
      list(GET release_libs ${i} release_lib)
      target_link_libraries(${this_target} debug ${debug_lib} optimized ${release_lib})
    endforeach()

  endfunction()

  # TODO: if we can make conan-libffi to work, remove this.
  set(FFI_ZIP_FILENAME "FFI_3_2_1-msvc2017_v2.zip")
  set(FFI_ZIP_EXPECTED_MD5 "9d43417932447eb5830a389273954a75")
  set(FFI_ZIP_LOCAL_PATH "${PROJECT_BINARY_DIR}/${FFI_ZIP_FILENAME}")
  if(EXISTS "${FFI_ZIP_LOCAL_PATH}")
    file(MD5 "${FFI_ZIP_LOCAL_PATH}" FFI_ZIP_MD5)
  endif()

  if(NOT FFI_ZIP_MD5 STREQUAL FFI_ZIP_EXPECTED_MD5)
    unset(FFI CACHE)
    unset(FFID CACHE)
    message(STATUS "Downloading FFI: ${FFI_ZIP_FILENAME}")
    file(DOWNLOAD "http://openstudio-resources.s3.amazonaws.com/dependencies/${FFI_ZIP_FILENAME}"
      ${FFI_ZIP_LOCAL_PATH}
      INACTIVITY_TIMEOUT 120
      SHOW_PROGRESS
      EXPECTED_MD5 ${FFI_ZIP_EXPECTED_MD5})

    file(REMOVE_RECURSE "${PROJECT_BINARY_DIR}/FFI-install")
    execute_process(COMMAND ${CMAKE_COMMAND} -E tar xfz ${FFI_ZIP_LOCAL_PATH} WORKING_DIRECTORY "${PROJECT_BINARY_DIR}")
  endif()

  find_library(FFI libffi.lib PATHS "${PROJECT_BINARY_DIR}/FFI-install/Release/lib")
  find_library(FFID libffi.lib PATHS "${PROJECT_BINARY_DIR}/FFI-install/Debug/lib")
  set(ADDITIONAL_RUBY_LIBS_RELEASE ${FFI} Iphlpapi)
  set(ADDITIONAL_RUBY_LIBS_DEBUG ${FFID} Iphlpapi)
  LINK_DEBUG_AND_RELEASE(additional_ruby_libs "${ADDITIONAL_RUBY_LIBS_DEBUG}" "${ADDITIONAL_RUBY_LIBS_RELEASE}")
endif()

if(APPLE)
  find_library(COREFOUNDATION_LIBRARY CoreFoundation )
  target_link_libraries(openstudio ${COREFOUNDATION_LIBRARY})
elseif (UNIX)
  target_link_libraries(additional_ruby_libs dl crypt)
  # target_link_libraries(openstudio "icui18n" "icuuc" "gmp")
elseif(WIN32)
  target_link_libraries(openstudio wsock32 ws2_32 Dbghelp Shlwapi)
  set_target_properties(openstudio PROPERTIES LINK_FLAGS_DEBUG "/NODEFAULTLIB:MSVCRT")
endif()
