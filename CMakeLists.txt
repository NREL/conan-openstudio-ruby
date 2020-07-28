cmake_minimum_required(VERSION 3.10.2)
cmake_policy(SET CMP0048 NEW)

project(openstudio_ruby)


include(ExternalProject)

option(INTEGRATED_CONAN "Use conan integrated into this CMake." ON)

set(OPENSSL_VERSION "1.1.0l")

if (INTEGRATED_CONAN)
  ###############################################################################
  # Conan

  # Download automatically, you can also just copy the conan.cmake file
  if(NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake")
    message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
    file(DOWNLOAD "https://github.com/conan-io/cmake-conan/raw/v0.14/conan.cmake"
      "${CMAKE_BINARY_DIR}/conan.cmake")
  endif()

  include(${CMAKE_BINARY_DIR}/conan.cmake)
  message("RUNNING CONAN")

  conan_check(VERSION 1.24.0 REQUIRED)

  conan_add_remote(NAME bincrafters
    URL https://api.bintray.com/conan/bincrafters/public-conan)
  
  # TODO: Temp
  conan_add_remote(NAME jmarrec
    URL https://api.bintray.com/conan/jmarrec/testing)

  #conan_add_remote(NAME jmarrec
  #  URL https://api.bintray.com/conan/jmarrec/testing)

  set(CONAN_BUILD "missing")
  if (APPLE)
    list(APPEND CONAN_BUILD "zlib")
  endif()
  list(APPEND CONAN_OPTIONS "zlib:minizip=True")
  list(APPEND CONAN_OPTIONS "gdbm:libgdbm_compat=True")
  list(APPEND CONAN_OPTIONS "gdbm:with_libiconv=False")
  list(APPEND CONAN_OPTIONS "gdbm:with_nls=False")

  # Passing shared=False is fine (but also already the default)
  # Passing fPIC=True is already the default on Unix, and doesn't exist on Windows (options is deleted in most recipes)
  #list(APPEND CONAN_OPTIONS "libyaml:fPIC=True")
  #list(APPEND CONAN_OPTIONS "libyaml:shared=False")
  #list(APPEND CONAN_OPTIONS "gdbm:fPIC=True")
  #list(APPEND CONAN_OPTIONS "gdbm:shared=False")
  #list(APPEND CONAN_OPTIONS "readline:fPIC=True")
  #list(APPEND CONAN_OPTIONS "readline:shared=False")
  #list(APPEND CONAN_OPTIONS "fPIC=True")
  #list(APPEND CONAN_OPTIONS "libffi:shared=False")

  if(NOT MSVC)
    set(CONAN_FFI "libffi/3.3")
    set(CONAN_LIBYAML "libyaml/0.2.2@bincrafters/stable")
    set(CONAN_READLINE "readline/8.0")
    list(APPEND CONAN_OPTIONS "gdbm:with_readline=True")
    set(CONAN_GDBM "gdbm/1.18.1")
    set(CONAN_GMP "gmp/6.2.0")
  endif()

  conan_cmake_run(REQUIRES
    openssl/${OPENSSL_VERSION}
    ruby_installer/2.5.5@bincrafters/stable
    # cant use bison/3.5.3 from CCI as it uses m4 which won't build with x86. So use bincrafters' still but explicitly add bin dir to PATH later
    # bison_installer/3.3.2@bincrafters/stable
    bison/3.5.3
    zlib/1.2.11
    ${CONAN_FFI}
    ${CONAN_LIBYAML}
    ${CONAN_READLINE}
    ${CONAN_GDBM}
    ${CONAN_GMP}

    BASIC_SETUP CMAKE_TARGETS NO_OUTPUT_DIRS
    GENERATORS cmake_find_package
    BUILD ${CONAN_BUILD}
  )
else()
  include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
endif()



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

macro(FindValue ValueName)
  set(LocalVar "")
  set(LocalVar $<$<CONFIG:Debug>:${${ValueName}_DEBUG}>$<$<CONFIG:Release>:${${ValueName}_RELEASE}>$<$<CONFIG:RelWithDebInfo>:${$ValueName}_RELWITHDEBINFO}>$<$<CONFIG:MinSizeRel>:${${ValueName}_MINSIZEREL}>
  )
#  list(JOIN LocalVar "" LocalVar)
  string(STRIP "${LocalVar}" LocalVar)
  set(CURRENT_${ValueName} $<IF:$<BOOL:${LocalVar}>,${LocalVar},${${ValueName}}>)
  # For debug purposes
  # message(STATUS "Found '${ValueName}' as '${CURRENT_${ValueName}}'")
endmacro()

FindValue(CMAKE_C_FLAGS)

FindValue(CONAN_OPENSSL_ROOT)
FindValue(CONAN_LIB_DIRS_OPENSSL)

FindValue(CONAN_ZLIB_ROOT)
FindValue(CONAN_LIB_DIRS_ZLIB)

FindValue(CONAN_LIBFFI_ROOT)
FindValue(CONAN_LIB_DIRS_LIBFFI)

FindValue(CONAN_BIN_DIRS_RUBY_INSTALLER)

FindValue(CONAN_LIBYAML_ROOT)
FindValue(CONAN_LIB_DIRS_LIBYAML)

FindValue(CONAN_GDBM_ROOT)
FindValue(CONAN_LIB_DIRS_GDBM)

FindValue(CONAN_READLINE_ROOT)
FindValue(CONAN_LIB_DIRS_READLINE)

FindValue(CONAN_GMP_ROOT)
FindValue(CONAN_LIB_DIRS_GMP)

FindValue(CONAN_BIN_DIRS_BISON_INSTALLER)

if(NOT UNIX)
  # conan-ffi doesn't link properly, so build from source.
  set(CURRENT_CONAN_LIBFFI_ROOT ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/)
  set(CURRENT_CONAN_LIB_DIRS_LIBFFI ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib)

  # Adjust build flags:
  # If these flags are not set correctly on Windows we get a failure to link
  string(REPLACE "/O2" "-O2sy-" CURRENT_CMAKE_C_FLAGS ${CURRENT_CMAKE_C_FLAGS})
  string(REPLACE "/Ob2" "" CURRENT_CMAKE_C_FLAGS ${CURRENT_CMAKE_C_FLAGS})
  string(REPLACE "/DNDEBUG" "" CURRENT_CMAKE_C_FLAGS ${CURRENT_CMAKE_C_FLAGS})
endif()

# TODO: there might be side effects supplying "with-xxx-dir=''" if not defined. Problem is that generator expressions are evaluated as build time... So need to wrap into another
# Note JM 2019-06-20: Please mind the space after the true_string arg.
# Notice that we pass --with-dbm-dir poiting to conan gdbm: that's because we build with gdbm_compat which should provide dbm too
# We also pass `--with-dbm-type=gdbm_compat` since we use GDBM > 1.8.1 (found this arg in `Ruby/ext/extconf.rb`)
# Note: probably would be a good idea to escape the path by wrapping into double quotes (for build_ruby.bat at least...)
set(CONF_ARGS
"$<IF:$<BOOL:${CURRENT_CONAN_ZLIB_ROOT}>,--with-zlib-dir=${CURRENT_CONAN_ZLIB_ROOT} ,>\
$<IF:$<BOOL:${CURRENT_CONAN_OPENSSL_ROOT}>,--with-openssl-dir=${CURRENT_CONAN_OPENSSL_ROOT} ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIBFFI_ROOT}>,--with-libffi-dir=${CURRENT_CONAN_LIBFFI_ROOT} ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIBYAML_ROOT}>,--with-libyaml-dir=${CURRENT_CONAN_LIBYAML_ROOT} ,>\
$<IF:$<BOOL:${CURRENT_CONAN_GDBM_ROOT}>,--with-gdbm-dir=${CURRENT_CONAN_GDBM_ROOT} ,>\
$<IF:$<BOOL:${CURRENT_CONAN_GDBM_ROOT}>,--with-dbm-dir=${CURRENT_CONAN_GDBM_ROOT} --with-dbm-type=gdbm_compat ,>\
$<IF:$<BOOL:${CURRENT_CONAN_READLINE_ROOT}>,--with-readline-dir=${CURRENT_CONAN_READLINE_ROOT} ,>\
$<IF:$<BOOL:${CURRENT_CONAN_GMP_ROOT}>,--with-gmp-dir=${CURRENT_CONAN_GMP_ROOT} ,>"
)

# openssl (> 1.1.0) from conan center index now renames debug libraries to libssld and libcryptod
FindValue(CONAN_LIBS_OPENSSL)
set(OPENSSL_LIBCRYPTO_NAME $<IF:$<CONFIG:Debug>,libcryptod,libcrypto>)
set(OPENSSL_LIBSSL_NAME $<IF:$<CONFIG:Debug>,libssld,libssl>)

# TODO: Unused right now
# TODO: once/if gdbm works on MSVC, check the gdbm_compat.lib name and others
set(EXTLIBS
"$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_ZLIB}>,${CURRENT_CONAN_LIB_DIRS_ZLIB}/zlib.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_OPENSSL}>,${CURRENT_CONAN_LIB_DIRS_OPENSSL}/${OPENSSL_LIBCRYPTO_NAME}.lib ${CURRENT_CONAN_LIB_DIRS_OPENSSL}/${OPENSSL_LIBSSL_NAME}.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_LIBFFI}>,${CURRENT_CONAN_LIB_DIRS_LIBFFI}/libffi.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_LIBYAML}>,${CURRENT_CONAN_LIB_DIRS_LIBYAML}/yaml.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_GDBM}>,${CURRENT_CONAN_LIB_DIRS_GDBM}/gdbm.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_GDBM}>,${CURRENT_CONAN_LIB_DIRS_GDBM}/gdbm_compat.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_READLINE}>,${CURRENT_CONAN_LIB_DIRS_READLINE}/readline.lib ,>\
$<IF:$<BOOL:${CURRENT_CONAN_LIB_DIRS_GMP}>,${CURRENT_CONAN_LIB_DIRS_GMP}/libgmp.lib ,> "
)

if( UNIX )
  # set(RUBY_EXT_CONFIG "")
  #if (NOT APPLE)
  #  # DLM: still missing: curses, dbm, gdbm
  #  # gbdm: libgbdm3 for Up to 16.04, libgbdm5 for 18.04
  #  # sudo apt-get -y install ruby autoconf automake libtool bison libgdbm-dev zlib1g-dev libLIBFFI-dev libssl-dev
  #  # sudo apt-get -y install build-essential libssl-dev libreadline-dev zlib1g-dev
  #  set(RUBY_EXT_CONFIG "--with-openssl-dir=/usr --with-readline-dir=/usr --with-zlib-dir=/usr")
  #endif()


  #if (APPLE)
    # Find some homebrew stuff
    # include(FindHomeBrewPackage.cmake)
  # endif()

    # KSB: For Mac, you may need to install some things...
  # brew install homebrew/dupes/zlib
  # brew link --overwrite --force homebrew/dupes/zlib
  # brew install autoconf automake libtool
  # brew link autoconf automake libtool

  set(configure_cmd "./configure --with-static-linked-ext ${MAC_opts} --disable-install-doc --prefix=${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install ${CONF_ARGS}")
  ExternalProject_Add(Ruby
    # Use official ruby source package to reduce dependencies on autoconf and friends
    URL https://cache.ruby-lang.org/pub/ruby/2.5/ruby-2.5.5.tar.gz
    URL_HASH SHA256=28a945fdf340e6ba04fc890b98648342e3cccfd6d223a48f3810572f11b2514c

    # The 'nodynamic' modules patch fails to build in any way on Unix, with 2.5.x, so we aren't using it (at the moment anyhow)
    PATCH_COMMAND pwd && ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.patch # && ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.nodynamic.patch
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND pwd && sh -c "pwd && echo '===============  CONFIGURE ============' && echo 'Calling: ${configure_cmd}' && ${configure_cmd}"
    #    BUILD_COMMAND ${CMAKE_MAKE_PROGRAM} Use default BUILD_COMMAND for now
    INSTALL_COMMAND ${CMAKE_MAKE_PROGRAM} install && sh -c "cp ./rbconfig.rb ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/ruby/2.5.0/." && sh -c "rm -rf ./ext/-test-" && sh -c "mkdir ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/ext" && sh -c "mkdir ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/enc" && sh -c "find ./ext -name '*.a' | xargs -I {} cp {} ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/ext/" && sh -c "find ./enc -name '*.a' | xargs -I {} cp {} ${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/enc"
    # Run a ruby script to ensure we linked against the right OpenSSL
    TEST_COMMAND sh -c "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/bin/ruby ${CMAKE_SOURCE_DIR}/test_openssl_version.rb ${OPENSSL_VERSION}"
  )
  find_file( RUBY_CONFIG_INCLUDE_DIR config.h PATHS "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/include/" )

else()
  # DLM notes:
  # @$(WIN32DIR:/=\)\rtname conftest.exe >>$(MAKEFILE) is used to determine which MSCV Runtime is linked

  # Post Build:
  # rename libs to : x64-msvcr140-ruby251.lib and x64-msvcr140-ruby251-static.lib
  # copy OpenSSL dlls into release and debug bin directories
  # patch config.h to allow for multiple _MSC_VER values:
  #   #if !(_MSC_VER == 1915 || _MSC_VER == 1916 || _MSC_VER == 1917 || _MSC_VER == 1918 || _MSC_VER == 1919)
  # tar -zcvf ruby_2_5_1_msvc2017_static.tar.gz Ruby-install

  # TODO: replace with conanfile.py: self.build_requires("bison_installer/3.3.2@bincrafters/stable")

  # get bison and sed tools
  # at least check if already there before redownloading (conanfile calls CMake.build twice right now!)
  if(NOT EXISTS ${CMAKE_BINARY_DIR}/tools)
    file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/tools)
  endif()
  #file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/bison/2.4.1/bison-2.4.1-bin.zip ${CMAKE_BINARY_DIR}/tools/bison-2.4.1-bin.zip)
  #file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/bison/2.4.1/bison-2.4.1-dep.zip ${CMAKE_BINARY_DIR}/tools/bison-2.4.1-dep.zip)
  if(NOT EXISTS ${CMAKE_BINARY_DIR}/tools/sed-4.2.1-dep.zip)
    file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/sed/4.2.1/sed-4.2.1-dep.zip ${CMAKE_BINARY_DIR}/tools/sed-4.2.1-dep.zip)
  endif()
  if(NOT EXISTS ${CMAKE_BINARY_DIR}/tools/sed-4.2.1-bin.zip)
    file(DOWNLOAD https://iweb.dl.sourceforge.net/project/gnuwin32/sed/4.2.1/sed-4.2.1-bin.zip ${CMAKE_BINARY_DIR}/tools/sed-4.2.1-bin.zip)
  endif()

  #add_custom_command(OUTPUT ${CMAKE_BINARY_DIR}/tools/bin/bison.exe ${CMAKE_BINARY_DIR}/tools/bin/sed.exe
      #COMMAND ${CMAKE_COMMAND} -E tar xvf bison-2.4.1-bin.zip
      #COMMAND ${CMAKE_COMMAND} -E tar xvf bison-2.4.1-dep.zip
      #COMMAND ${CMAKE_COMMAND} -E tar xvf sed-4.2.1-bin.zip
      #COMMAND ${CMAKE_COMMAND} -E tar xvf sed-4.2.1-dep.zip
      #WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tools)
  #add_custom_target(GetTools
      #DEPENDS ${CMAKE_BINARY_DIR}/tools/bin/bison.exe)

  add_custom_command(OUTPUT ${CMAKE_BINARY_DIR}/tools/bin/sed.exe
      COMMAND ${CMAKE_COMMAND} -E tar xvf sed-4.2.1-bin.zip
      COMMAND ${CMAKE_COMMAND} -E tar xvf sed-4.2.1-dep.zip
      WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tools)
  add_custom_target(GetTools
      DEPENDS ${CMAKE_BINARY_DIR}/tools/bin/sed.exe)

  set(ARCH "x64")
  set(FFI_LIB_FOLDER "x64/")
  if("${CMAKE_SIZEOF_VOID_P}" STREQUAL "4")
    set(ARCH "x86")
    set(FFI_LIB_FOLDER "")
  endif()

  ## The libFFI provided by Conan gives us something we cannot link to for some reason (TBD)
  ## It's possible we can move to the in-built deps provided by ruby
  ExternalProject_Add(FFI
    URL_HASH SHA256=bf6813045c0d470aedc3c69f9ec11fe351c2d7360c7d5396dc9a6ddc4830033c
    URL https://github.com/winlibs/libffi/archive/libffi-3.2.1.zip
    CONFIGURE_COMMAND ""
    BUILD_COMMAND devenv /upgrade ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_${ARCH}/libffi-msvc.sln
      COMMAND msbuild ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_${ARCH}/libffi-msvc.sln /p:Configuration=$<CONFIG> /p:DefineConstants="FFI_BUILDING" "/p:Platform=${CMAKE_VS_PLATFORM_NAME}" "/p:WindowsTargetPlatformVersion=${CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION}"
    INSTALL_COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/
      COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/
      COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/include ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/include
      COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/fficonfig.h ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/include/fficonfig.h
      COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/src/x86/ffitarget.h ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/include/ffitarget.h
      COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib
      COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_${ARCH}/${FFI_LIB_FOLDER}$<CONFIG>/libffi.lib ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib/libffi.lib
      #COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI/win32/vc14_${ARCH}/${FFI_LIB_FOLDER}$<CONFIG>/libffi.pdb ${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib/libffi.pdb
  )

  configure_file("build_ruby.bat.in" "${CMAKE_BINARY_DIR}/build_ruby.bat.out")
  file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/build_ruby_$<CONFIG>.bat"
                INPUT "${CMAKE_BINARY_DIR}/build_ruby.bat.out")

  # TODO: consider moving to the official ruby distribution and avoid needing the above
  # tool dependencies
  ExternalProject_Add(Ruby
    DEPENDS GetTools FFI
    #    URL https://cache.ruby-lang.org/pub/ruby/2.5/ruby-2.5.5.tar.gz
    #    URL_HASH SHA256=28a945fdf340e6ba04fc890b98648342e3cccfd6d223a48f3810572f11b2514c
    URL https://codeload.github.com/ruby/ruby/tar.gz/v2_5_5
    URL_HASH SHA256=A3BA7160C7E0CE03865CDABA9B7C26974A8A0FC23FC953269E0463C5ACAFB7A1
    PATCH_COMMAND ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.patch && ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.win.patch && ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.win.CCI.patch  # && ${PATCH_EXE} -p1 < ${CMAKE_SOURCE_DIR}/Ruby.nodynamic.patch
    CONFIGURE_COMMAND ""
    BUILD_COMMAND cmd /C "${CMAKE_BINARY_DIR}/build_ruby_$<CONFIG>.bat"
    INSTALL_COMMAND ${CMAKE_COMMAND} -E copy "${CMAKE_BINARY_DIR}/FFI-prefix/src/FFI-install/$<CONFIG>/lib/libffi.lib" "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/lib/"
    # Run a ruby script to ensure we linked against the right OpenSSL
    TEST_COMMAND cmd /C "${CMAKE_BINARY_DIR}/Ruby-prefix/src/Ruby-install/bin/ruby ${CMAKE_SOURCE_DIR}/test_openssl_version.rb ${OPENSSL_VERSION}"
  )
endif()
