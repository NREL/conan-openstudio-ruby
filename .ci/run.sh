#!/usr/bin/env bash

set -ex

if [[ "$(uname -s)" == 'Darwin' ]]; then
    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi
    pyenv activate conan
fi

# The CONAN_ENV_COMPILER_LIBCXX is being ignored, so we reset it
echo "Setting the settigns.compiler.libcxx=$CONAN_ENV_COMPILER_LIBCXX"
conan profile update settings.compiler.libcxx=$CONAN_ENV_COMPILER_LIBCXX default

python build.py
