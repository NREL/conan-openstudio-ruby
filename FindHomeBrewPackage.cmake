if (APPLE)
  # Find some homebrew stuff
  include(FindPackageMessage)

  find_program(brew brew)
  if(brew)
    find_package_message(brew "Homebrew found: ${brew}" "1;${brew}")
  else()
    find_package_message(brew "Homebrew not found" "0")
    return()
  endif()

  set(REQUIRED_BREW_LIBS
    gdbm
    libyaml
    libffi
    readline
    # openssl is from conan
  )

  foreach(brew_lib ${REQUIRED_BREW_LIBS})
    execute_process(COMMAND "${brew}" --prefix "${brew_lib}"
      RESULT_VARIABLE status_code
      OUTPUT_VARIABLE brew_lib_loc OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
    if(status_code EQUAL 0)
      find_package_message(status_code "${brew_lib} via Homebrew: ${brew_lib_loc}"
        "${brew_lib_loc}")
      set(MAC_opts "${MAC_opts} --with-${brew_lib}-dir=${brew_lib_loc}")
    else()
      message("Returned with code ${status_code}")
      message(FATAL_ERROR "Please use homebrew to install ${brew_lib}: `brew install ${brew_lib}`")
    endif()
  endforeach()

  message(STATUS "Configuring Ruby with Mac Options: '${MAC_opts}")
endif()
