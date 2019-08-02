#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from cpt.ci_manager import GenericManager
from bincrafters import build_template_default

if __name__ == "__main__":

    # CONAN_STABLE_PATTERN env variable is used to set:
    # * branch `master` to upload to `stable`
    # * All other to `testing`
    # Here we also check the branch, and if not master or develop, don't upload
    branch = GenericManager(None).get_branch()
    if branch in ['master', 'develop']:
        upload_only_when_stable = False
    else:
        # It can't be stable since that means it'd be 'master' => never upload
        upload_only_when_stable = True

    # Pending https://github.com/bincrafters/bincrafters-package-tools/pull/25
    # We can't use this upload_only_when_stable param so instead we set it as
    # an env var
    os.environ["CONAN_UPLOAD_ONLY_WHEN_STABLE"] = upload_only_when_stable

    # This will add common builds.
    # We are customizing what these are by using environment variables.
    # Because we pass:
    # * CONAN_ARCHS=x86_64, it will only produce the x64
    # * CONAN_APPLE_CLANG_VERSIONS/CONAN_GCC_VERSIONS/CONAN_VISUAL_VERSIONS,
    #   it will only use the specific one that's passed
    # * CONAN_BUILD_TYPES, it will limit itself to the ones we asked
    # cf: https://github.com/conan-io/conan-package-tools
    # Specifically in ./cpt/builds_generator.py

    builder = build_template_default.get_builder(build_policy="outdated",
                                                 # upload_only_when_stable=upload_only_when_stable,
    builder.run()
