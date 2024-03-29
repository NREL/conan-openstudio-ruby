cmake_minimum_required(VERSION 3.10.2)

set(CMAKE_CXX_STANDARD 11)

add_executable(CreateEmbeddedSource
  CreateEmbeddedSource.cpp
)

target_link_libraries(CreateEmbeddedSource PRIVATE CONAN_PKG::zlib)
if (MSVC)
  target_link_libraries(CreateEmbeddedSource PRIVATE -IGNORE:4099)
endif()

# Add a specific manifest for CreateEmbeddedSource that will include the LongPathAware attribute, which,
# in conjunction with the regkey LongPathsEnabled=1 will make it work with paths that are longer than MAX_PATH (win10 only)
if( WIN32 )
  add_custom_command(TARGET CreateEmbeddedSource
    POST_BUILD
    COMMAND  mt -nologo -manifest "${CMAKE_CURRENT_SOURCE_DIR}/CreateEmbeddedSource.manifest.xml" -outputresource:$<TARGET_FILE:CreateEmbeddedSource>
  )
endif()
