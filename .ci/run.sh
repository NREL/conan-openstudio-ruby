#!/usr/bin/env bash

set -ex

if [[ "$(uname -s)" == 'Darwin' ]]; then
    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi
    pyenv activate conan
fi

python build.py

if [[ "$(uname -s)" == 'Darwin' ]]; then
  find ~/.conan/data/openstudio_ruby/2.5.5/nrel/testing/build/*/Ruby-prefix/src/Ruby/ext/gdbm -name “mkmf.log”
  find . -name "*.yml"|while read fname; do
    echo "============== $fname ============"
    cat $fname
    echo ""
    echo ""
    echo ""
  done
fi
