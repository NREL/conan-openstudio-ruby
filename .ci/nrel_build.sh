#!/usr/bin/env bash

CONAN_PKG_NAM=openstudio_ruby
RUBY_VERSION=2.5.5
GIT_SHA_SHORT=$(git rev-parse --short=10 HEAD)
CONAN_REPO=openstudio
CONAN_CHANNEL=testing
CONAN_USER=commercialbuilding

conan remote add ${CONAN_REPO} https://api.bintray.com/conan/commercialbuilding/openstudio

conan user -p ${BINTRAY_API} -r ${CONAN_REPO} ${CONAN_USER}

conan create . $CONAN_PKG_NAM/${RUBY_VERSION}-${GIT_SHA_SHORT}@${CONAN_REPO}/${CONAN_CHANNEL}

conan upload "$CONAN_PKG_NAM/${RUBY_VERSION}-${GIT_SHA_SHORT}@${CONAN_REPO}/${CONAN_CHANNEL}" -r ${CONAN_REPO}

