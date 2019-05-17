import os
import glob as gb
from conans import ConanFile, CMake


class OpenstudiorubyConan(ConanFile):
    name = "openstudio_ruby"
    version = "2.5.5"
    license = "<Put the package license here>"
    author = "<Put your name here> <And your email here>"
    url = "<Package recipe repository url here, for issues about the package>"
    description = "<Description of Openstudioruby here>"
    topics = ("<Put some tag here>", "<here>", "<and here>")
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = "*"
    generators = "cmake"

    def configure(self):
        self.requires("OpenSSL/1.1.0g@conan/stable")
        self.requires("ruby_installer/2.5.1@bincrafters/stable")
        self.requires("zlib/1.2.11@conan/stable")

    def build(self):
        cmake = CMake(self)
        cmake.definitions["INTEGRATED_CONAN"] = False
        cmake.configure()

        # On Windows the build never succeeds on the first try. Much effort
        # was spent trying to figure out why. This is the compromise:
        # we just build twice.
        try:
            cmake.build()
        except:
            # total hack to allow second attempt at building
            self.should_build = True
            cmake.build()

    def package(self):
        self.copy("*", src="Ruby-prefix/src/Ruby-install", keep_path=True)

    def find_config_header(self):
        """
        Locate the ruby/config.h which will be in different folders depending
        on the platform
        """
        found = gb.glob("**/ruby/config.h", recursive=True)
        if len(found) != 1:
            raise "Didn't find one and one only ruby/config.h"

        p = found[0]
        abspath = os.path.abspath(os.path.join(p, os.pardir, os.pardir))
        relpath = os.path.relpath(abspath, ".")
        # Add a success (in green) to ensure it did the right thing
        self.output.success("Found config.h in {}".format(relpath))
        return relpath

    def package_info(self):
        # TODO: This can certainly be done better with file globbing
        # or something

        if self.settings.os == "Windows":
            libext = "lib"

        else:
            libext = "a"

        # Note: If you don't specify explicitly self.package_folder, "."
        # actually already resolves to it when package_info is run

        # Glob all libraries, keeping only their name (and not the path)
        glob_pattern = "**/*.{}".format(libext)
        # glob_pattern = os.path.join(self.package_folder, glob_pattern)

        libs = gb.glob(glob_pattern, recursive=True)
        if not libs:
            # Add debug info
            self.output.info("cwd={}".format(os.path.abspath(".")))
            self.output.info("Package folder: {}".format(self.package_folder))
            self.output.error("Globbing: {}".format(glob_pattern))
            raise "Didn't find the libraries!"

        self.output.success("Found {} libs".format(len(libs)))

        # Relative to package folder: no need unless explicitly setting glob
        # to package_folder above
        # libs = [os.path.relpath(p, start=self.package_folder) for p in libs]

        # Keep only the names
        self.cpp_info.libs = [os.path.basename(x) for x in libs]

        # self.cpp_info.libdirs = ['lib', 'lib/ext', 'lib/enc']
        # Equivalent automatic detection
        # list of unique folders
        libdirs = list(set([os.path.dirname(x) for x in libs]))
        # Sort it by nesting level, smaller first
        libdirs.sort(key=lambda p: len(os.path.normpath(p).split(os.sep)))
        self.cpp_info.libdirs = libdirs

        self.output.info("cpp_info.libs = {}".format(self.cpp_info.libs))

        # include/ruby-2.5.0/x64-mswin64_140'
        # 'include/ruby-2.5.0/x86_64-linux',
        # 'include/ruby-2.5.0/x86_64-darwin17'

        self.cpp_info.includedirs = ['include', 'include/ruby-2.5.0']
        self.cpp_info.includedirs.append(self.find_config_header())
