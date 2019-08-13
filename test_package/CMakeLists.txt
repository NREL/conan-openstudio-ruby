project(test_package)
cmake_minimum_required(VERSION 3.10.2)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

message("CONAN_LIBS=${CONAN_LIBS}")



CONFIGURE_FILE_WITH_CHECKSUM("InitMacros.hxx.in" "${CMAKE_CURRENT_BINARY_DIR}/InitMacros.hxx")

set(MODULE_ROOT "${CONAN_OPENSTUDIO_RUBY_ROOT}")
if ("${MODULE_ROOT}" STREQUAL "")
  set(MODULE_ROOT "${CONAN_OPENSTUDIO_RUBY_ROOT_DEBUG}")
endif()

message("Searching for ruby modules in '${MODULE_ROOT}/lib/**/*.rb'")
file(GLOB_RECURSE  EXTENSION_RB  FOLLOW_SYMLINKS "${MODULE_ROOT}/lib/**/*.rb")

include_directories(${CMAKE_CURRENT_BINARY_DIR} ${PROJECT_BINARY_DIR} ${PROJECT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR} )

add_executable(openstudio
  main.cpp
  # "${CMAKE_CURRENT_BINARY_DIR}/SWIGRubyRuntime.hxx"
  RubyException.hpp
  RubyInterpreter.hpp
  # "${CMAKE_CURRENT_BINARY_DIR}/embedded_scripting_wrap.cxx"
  ${OUTPUT}
)

target_link_libraries(${PROJECT_NAME} CONAN_PKG::openstudio_ruby)
