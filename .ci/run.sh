#!/usr/bin/env bash

# -e: exit as soon as one command fails
# -x: print each command about to be execute with a leading "+"
set -ex

if [[ "$(uname -s)" == 'Darwin' ]]; then
    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi
    pyenv activate conan
fi

python build.py

# Debug: how to retrieve logs: remove the "-e" option above, then cat the logs you want:

#if [[ "$(uname -s)" == 'Darwin' ]]; then
  #find ~/.conan/data/openstudio_ruby/2.5.5/nrel/testing/build -name "mkmf.log"|while read fname; do
    #echo "============== $fname ============"
    #cat $fname
    #echo ""
    #echo ""
    #echo ""
  #done

  #echo "======== LISTING THE GDBM LIB FOLDERS ========"
  #find ~/.conan/data/gdbm/1.18.1/_/_/package/ -name 'lib' -type 'd'|while read dirname; do
    #echo $dirname
    #ls $dirname
    #echo ""
    #echo ""
    #echo ""
  #done

  #echo "======== LISTING THE GDBM INCLUDE FOLDERS ========"
  #find ~/.conan/data/gdbm/1.18.1/_/_/package/ -name 'include' -type 'd'|while read dirname; do
    #echo $dirname
    #ls $dirname
    #echo ""
    #echo ""
    #echo ""
  #done

  #echo "=========== RUBY CONFIG.LOG ================"
  #find ~/.conan/data/openstudio_ruby/2.5.5/nrel/testing/build -name "config.log"|while read fname; do
    #echo "============== $fname ============"
    #cat $fname
    #echo ""
    #echo ""
    #echo ""
  #done

  #echo "=========== RUBY CONFIG.STATUS ================"
  #find ~/.conan/data/openstudio_ruby/2.5.5/nrel/testing/build -name "config.status"|while read fname; do
    #echo "============== $fname ============"
    #cat $fname
    #echo ""
    #echo ""
    #echo ""
  #done
#fi
