#!/usr/bin/env bash
set -e

CONAN_PKG_NAM=openstudio_ruby
RUBY_VERSION=2.5.5
GIT_SHA_SHORT=$(git rev-parse --short=10 HEAD)
CONAN_REPO=openstudio
CONAN_CHANNEL=testing
CONAN_USER=commercialbuilding

# add  repos and igonore failures if already added
set +e
conan remote add bincrafters https://api.bintray.com/conan/bincrafters/public-conan
conan remote add conan-center https://conan.bintray.com
conan remote add ${CONAN_REPO} https://api.bintray.com/conan/commercialbuilding/openstudio

set -e
#log into conan
conan user -p ${BINTRAY_API} -r ${CONAN_REPO} ${CONAN_USER}

#create packages
conan create . $CONAN_PKG_NAM/${RUBY_VERSION}-${GIT_SHA_SHORT}@${CONAN_REPO}/${CONAN_CHANNEL}

#upload to commercialbuilding/openstudip
conan upload "$CONAN_PKG_NAM/${RUBY_VERSION}-${GIT_SHA_SHORT}@${CONAN_REPO}/${CONAN_CHANNEL}" -r ${CONAN_REPO}

