cmake_minimum_required(VERSION 3.10.2)
cmake_policy(SET CMP0048 NEW)

project(OpenStudio-Ruby VERSION 2.5.5)

include(ExternalProject)


###############################################################################
# Conan

# Download automatically, you can also just copy the conan.cmake file
if(NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake")
  message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
  file(DOWNLOAD "https://github.com/conan-io/cmake-conan/raw/v0.13/conan.cmake"
    "${CMAKE_BINARY_DIR}/conan.cmake")
endif()

include(${CMAKE_BINARY_DIR}/conan.cmake)

message("RUNNING CONAN")

conan_check(VERSION 1.0.0 REQUIRED)

conan_add_remote(NAME bincrafters
  URL https://api.bintray.com/conan/bincrafters/public-conan)
 

conan_cmake_run(REQUIRES 
  OpenSSL/1.1.0g@conan/stable
  ruby_installer/2.5.1@bincrafters/stable 
  zlib/1.2.11@conan/stable
  
  BASIC_SETUP CMAKE_TARGETS NO_OUTPUT_DIRS
  GENERATORS cmake_find_package
  BUILD missing
)

set(CMAKE_MODULE_PATH "${CMAKE_BINARY_DIR}")

find_package(OpenSSL)
find_package(zlib)
find_package(libffi)


find_package(Git)
if(NOT GIT_FOUND)
  find_program(GIT_EXECUTABLE git HINTS "$ENV{LOCALAPPDATA}/Programs/git/bin" "C:/Program Files/Git/bin")
  if(NOT GIT_EXECUTABLE_NOTFOUND)
    set(GIT_FOUND TRUE)
  endif()
endif()

if(GIT_FOUND)
  get_filename_component(GIT_DIR "${GIT_EXECUTABLE}" DIRECTORY)
else()
  set(GIT_DIR "")
endif()

find_program(PATCH_EXE patch HINTS "${GIT_DIR}" "${GIT_DIR}/../bin/" "${GIT_DIR}/../usr/bin/")
string(COMPARE EQUAL "${PATCH_EXE}" "PATCH_EXE-NOTFOUND" PATCH_EXE_NOTFOUND)
if(PATCH_EXE_NOTFOUND)
  message(SEND_ERROR "Required program patch not found")
endif()


set(CURRENT_C_FLAGS 
   $<$<CONFIG:Debug>:${CMAKE_C_FLAGS_DEBUG}>
   $<$<CONFIG:Release>:${CMAKE_C_FLAGS_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CMAKE_C_FLAGS_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CMAKE_C_FLAGS_MINSIZEREL}>
)
list(JOIN CURRENT_C_FLAGS "" CURRENT_C_FLAGS)

set(CURRENT_OPENSSL_DIR
   $<$<CONFIG:Debug>:${CONAN_OPENSSL_ROOT_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_OPENSSL_ROOT_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_OPENSSL_ROOT_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_OPENSSL_ROOT_MINSIZEREL}>
)
list(JOIN CURRENT_OPENSSL_DIR "" CURRENT_OPENSSL_DIR)


set(CURRENT_OPENSSL_LIB_DIR
   $<$<CONFIG:Debug>:${CONAN_LIB_DIRS_OPENSSL_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_LIB_DIRS_OPENSSL_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_LIB_DIRS_OPENSSL_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_LIB_DIRS_OPENSSL_MINSIZEREL}>
)
list(JOIN CURRENT_OPENSSL_LIB_DIR "" CURRENT_OPENSSL_LIB_DIR)

set(CURRENT_ZLIB_DIR
   $<$<CONFIG:Debug>:${CONAN_ZLIB_ROOT_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_ZLIB_ROOT_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_ZLIB_ROOT_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_ZLIB_ROOT_MINSIZEREL}>
)
list(JOIN CURRENT_ZLIB_DIR "" CURRENT_ZLIB_DIR)

set(CURRENT_ZLIB_LIB_DIR
   $<$<CONFIG:Debug>:${CONAN_LIB_DIRS_ZLIB_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_LIB_DIRS_ZLIB_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_LIB_DIRS_ZLIB_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_LIB_DIRS_ZLIB_MINSIZEREL}>
)
list(JOIN CURRENT_ZLIB_LIB_DIR "" CURRENT_ZLIB_LIB_DIR)

set(CURRENT_LIBFFI_DIR
   $<$<CONFIG:Debug>:${CONAN_LIBFFI_ROOT_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_LIBFFI_ROOT_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_LIBFFI_ROOT_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_LIBFFI_ROOT_MINSIZEREL}>
)
list(JOIN CURRENT_LIBFFI_DIR "" CURRENT_LIBFFI_DIR)

set(CURRENT_LIBFFI_LIB_DIR
   $<$<CONFIG:Debug>:${CONAN_LIB_DIRS_LIBFFI_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_LIB_DIRS_LIBFFI_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_LIB_DIRS_LIBFFI_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_LIB_DIRS_LIBFFI_MINSIZEREL}>
)
list(JOIN CURRENT_LIBFFI_LIB_DIR "" CURRENT_LIBFFI_LIB_DIR)

set (CURRENT_RUBY_BIN_DIR
   $<$<CONFIG:Debug>:${CONAN_BIN_DIRS_RUBY_INSTALLER_DEBUG}>
   $<$<CONFIG:Release>:${CONAN_BIN_DIRS_RUBY_INSTALLER_RELEASE}>
   $<$<CONFIG:RelWithDebInfo>:${CONAN_BIN_DIRS_RUBY_INSTALLER_RELWITHDEBINFO}>
   $<$<CONFIG:MinSizeRel>:${CONAN_BIN_DIRS_RUBY_INSTALLER_MINSIZEREL}>
)
list(JOIN CURRENT_RUBY_BIN_DIR "" CURRENT_RUBY_BIN_DIR)



if( UNIX )
  set(RUBY_EXT_CONFIG "")
  #if (NOT APPLE)
  #  # DLM: still missing: curses, dbm, gdbm
  #  # gbdm: libgbdm3 for Up to 16.04, libgbdm5 for 18.04
  #  # sudo apt-get -y install ruby autoconf automake libtool bison libgdbm-dev zlib1g-dev libLIBFFI-dev libssl-dev
  #  # sudo apt-get -y install build-essential libssl-dev libreadline-dev zlib1g-dev
  #  set(RUBY_EXT_CONFIG "--with-openssl-dir=/usr --with-readline-dir=/usr --with-zlib-dir=/usr")
  #endif()

  # KSB: For Mac, you may need to install some things...
  # brew install homebrew/dupes/zlib
  # brew link --overwrite --force homebrew/dupes/zlib
  # brew install autoconf automake libtool
  # brew link autoconf automake libtool
  ExternalProject_Add(Ruby
    URL https://codeload.github.com/ruby/ruby/tar.gz/v2_5_5
    URL_HASH SHA256=A3BA7160C7E0CE03865CDABA9B7C26974A8A0FC23FC953269E0463C5ACAFB7A1
    BUILD_IN_SOURCE 1
    PATCH_COMMAND ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/dependencies/ruby/Ruby.patch
    CONFIGURE_COMMAND sh -c "./configure --with-static-linked-ext ${RUBY_EXT_CONFIG} --disable-install-doc --prefix=${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install"
    BUILD_COMMAND ${MAKE}
    INSTALL_COMMAND ${MAKE} install && sh -c "cp ./rbconfig.rb ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/ruby/2.5.0/." && sh -c "rm -rf ./ext/-test-" && sh -c "mkdir ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/ext" && sh -c "mkdir ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/enc" && sh -c "find ./ext -name '*.a' | xargs -I {} cp {} ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/ext/" && sh -c "find ./enc -name '*.a' | xargs -I {} cp {} ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/enc"
  )
  find_file( RUBY_CONFIG_INCLUDE_DIR config.h PATHS "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/include/" )
  set(RUBY_LIBRARY "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/libruby-static.a") # TODO: might be libruby.2.5.1-static.a on Mac
  set(RUBY_INCLUDE_DIR "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/include/ruby-2.5.0")
  set(RUBY_EXECUTABLE "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/bin/ruby")
  set(RUBY_SOURCE_DIR "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby")
  set(RUBY_INSTALL_DIR "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install")

else()  
  # DLM notes:
  # @$(WIN32DIR:/=\)\rtname conftest.exe >>$(MAKEFILE) is used to determine which MSCV Runtime is linked
  
  # Post Build:
  # rename libs to : x64-msvcr140-ruby251.lib and x64-msvcr140-ruby251-static.lib 
  # copy OpenSSL dlls into release and debug bin directories
  # patch config.h to allow for multiple _MSC_VER values: 
  #   #if !(_MSC_VER == 1915 || _MSC_VER == 1916 || _MSC_VER == 1917 || _MSC_VER == 1918 || _MSC_VER == 1919)
  # tar -zcvf ruby_2_5_1_msvc2017_static.tar.gz Ruby-install    

  file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/tools)
  file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/bison/2.4.1/bison-2.4.1-bin.zip ${CMAKE_BINARY_DIR}/tools/bison-2.4.1-bin.zip)
  file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/bison/2.4.1/bison-2.4.1-dep.zip ${CMAKE_BINARY_DIR}/tools/bison-2.4.1-dep.zip)
  file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/sed/4.2.1/sed-4.2.1-dep.zip ${CMAKE_BINARY_DIR}/tools/sed-4.2.1-dep.zip)
  file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/sed/4.2.1/sed-4.2.1-bin.zip ${CMAKE_BINARY_DIR}/tools/sed-4.2.1-bin.zip)

  add_custom_command(OUTPUT ${CMAKE_BINARY_DIR}/tools/bin/bison.exe ${CMAKE_BINARY_DIR}/tools/bin/sed.exe
      COMMAND ${CMAKE_COMMAND} -E tar xvf bison-2.4.1-bin.zip
      COMMAND ${CMAKE_COMMAND} -E tar xvf bison-2.4.1-dep.zip
      COMMAND ${CMAKE_COMMAND} -E tar xvf sed-4.2.1-bin.zip
      COMMAND ${CMAKE_COMMAND} -E tar xvf sed-4.2.1-dep.zip
      WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tools)
  add_custom_target(GetTools
      DEPENDS ${CMAKE_BINARY_DIR}/tools/bin/bison.exe)


  # The libFFI provided by Conan gives us something we cannot link to for some reason (TBD)
  ExternalProject_Add(FFI
    URL_HASH SHA256=bf6813045c0d470aedc3c69f9ec11fe351c2d7360c7d5396dc9a6ddc4830033c
    URL https://github.com/winlibs/libffi/archive/libffi-3.2.1.zip
    CONFIGURE_COMMAND ""
    BUILD_COMMAND devenv /upgrade ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_x64/libffi-msvc.sln 
      COMMAND msbuild ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_x64/libffi-msvc.sln /p:Configuration=$<CONFIG> /p:DefineConstants="FFI_BUILDING" "/p:Platform=${CMAKE_VS_PLATFORM_NAME}" "/p:WindowsTargetPlatformVersion=${CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION}"
    INSTALL_COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/
      COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/include ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/include
      COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/fficonfig.h ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/include/fficonfig.h         
      COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/src/x86/ffitarget.h ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/include/ffitarget.h                 
      COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib
      COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_x64/x64/$<CONFIG>/libffi.lib ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib/libffi.lib 
      #COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_x64/x64/$<CONFIG>/libffi.pdb ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib/libffi.pdb 
  )

  set(CURRENT_LIBFFI_DIR ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/)
  set(CURRENT_LIBFFI_LIB_DIR ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib)

  configure_file("build_ruby.bat.in" "${CMAKE_BINARY_DIR}/build_ruby.bat.out")
  file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/build_ruby_$<CONFIG>.bat"
                INPUT "${CMAKE_BINARY_DIR}/build_ruby.bat.out")


  ExternalProject_Add(Ruby
    DEPENDS GetTools FFI
    URL https://codeload.github.com/ruby/ruby/tar.gz/v2_5_5
    URL_HASH SHA256=A3BA7160C7E0CE03865CDABA9B7C26974A8A0FC23FC953269E0463C5ACAFB7A1
    BUILD_IN_SOURCE 1
    PATCH_COMMAND ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.patch && ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.win.patch && ${PATCH_EXE} 

    CONFIGURE_COMMAND ""
    BUILD_COMMAND cmd /C "${CMAKE_BINARY_DIR}/build_ruby_$<CONFIG>.bat"
    INSTALL_COMMAND ""
  )
  set(RUBY_INSTALL_DIR "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/$<CONFIG>")
endif()
