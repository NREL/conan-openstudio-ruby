#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bincrafters import build_template_default

if __name__ == "__main__":

    # This will add common builds.
    # We are customizing what these are by using environment variables.
    # Because we pass:
    # * CONAN_ARCHS=x86_64, it will only produce the x64
    # * CONAN_APPLE_CLANG_VERSIONS/CONAN_GCC_VERSIONS/CONAN_VISUAL_VERSIONS,
    #   it will only use the specific one that's passed
    # * CONAN_BUILD_TYPES, it will limit itself to the ones we asked
    # cf: https://github.com/conan-io/conan-package-tools
    # Specifically in ./cpt/builds_generator.py
    builder = build_template_default.get_builder(build_policy="outdated")
    builder.run()
