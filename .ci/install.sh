#!/usr/bin/env bash

set -ex

unameOut="$(uname -s)"
case "${unameOut}" in
  Linux*)     machine=Linux;;
  Darwin*)    machine=Darwin;;
  CYGWIN*|MINGW*|MSYS*)    machine=Windows;;
  *)          machine="UNKNOWN:${unameOut}"
esac


if [[ $machine == Darwin ]]; then
  brew update || brew update
  brew outdated pyenv || brew upgrade pyenv
  brew install pyenv-virtualenv
  brew install cmake || true

  if which pyenv > /dev/null; then
    eval "$(pyenv init -)"
  fi

  pyenv install 3.7.1
  pyenv virtualenv 3.7.1 conan
  pyenv rehash
  pyenv activate conan
elif [[ $machine == Linux ]]; then
  apt install libgdbm-dev
fi

pip install conan --upgrade
pip install conan_package_tools bincrafters_package_tools
# Creates the conan data directory
conan user
