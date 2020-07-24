#!/usr/bin/env bash

# -e: exit as soon as one command fails
# -x: print each command about to be execute with a leading "+"
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi
    pyenv activate conan
fi

python build.py

if [[ "$(uname -s)" == 'Darwin' ]]; then
  find ~/.conan/data/openstudio_ruby/2.5.5/nrel/testing/build -name "mkmf.log"|while read fname; do
    echo "============== $fname ============"
    cat $fname
    echo ""
    echo ""
    echo ""
  done
fi
