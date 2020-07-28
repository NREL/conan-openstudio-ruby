#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from cpt.printer import Printer
from cpt.ci_manager import CIManager
from bincrafters import build_template_default

if __name__ == "__main__":

    # CONAN_STABLE_PATTERN env variable is used to set:
    # * branch `master` to upload to `stable`
    # * All other to `testing`
    # Here we also check the branch, and if not master or develop, don't upload
    printer = Printer()
    branch = CIManager(printer).get_branch()

    if branch in ['master', 'develop']:
        upload_only_when_stable = False
    else:
        # It can't be stable since that means it'd be 'master' => never upload
        upload_only_when_stable = True

    # Pending https://github.com/bincrafters/bincrafters-package-tools/pull/25
    # We can't use this upload_only_when_stable param so instead we set it as
    # an env var
    os.environ["CONAN_UPLOAD_ONLY_WHEN_STABLE"] = str(int(upload_only_when_stable))

    # This will add common builds.
    # We are customizing what these are by using environment variables.
    # Because we pass:
    # * CONAN_ARCHS=x86_64, it will only produce the x64
    # * CONAN_APPLE_CLANG_VERSIONS/CONAN_GCC_VERSIONS/CONAN_VISUAL_VERSIONS,
    #   it will only use the specific one that's passed
    # * CONAN_BUILD_TYPES, it will limit itself to the ones we asked
    # cf: https://github.com/conan-io/conan-package-tools
    # Specifically in ./cpt/builds_generator.py

    # When pure_c is False, it  will create, for GCC >=5, one build for
    # compiler.libcxx=libstdc++ and one for compiler.libcxx=libstc++11.
    # Then we filter the old ABI ones out since that will never happen
    # when run from OpenStudio's CMake
    # cf: https://docs.conan.io/en/latest/howtos/manage_gcc_abi.html
    pure_c = False

    builder = build_template_default.get_builder(build_policy="outdated",
                                                 # upload_only_when_stable=upload_only_when_stable,
                                                 pure_c=pure_c)
    builder.remove_build_if(
        lambda build: (build.settings["compiler"] == "gcc") and
                      (build.settings["compiler.libcxx"] != "libstdc++11")
    )

    builder.run()
