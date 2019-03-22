
#!/bin/bash

set -e
set -x

SUDO=sudo

if [[ "$(uname -s)" == 'Darwin' ]]; then
    brew update || brew update
    brew install cmake || true
    SUDO=
fi

$SUDO pip install conan --upgrade
$SUDO pip install conan_package_tools
conan user
