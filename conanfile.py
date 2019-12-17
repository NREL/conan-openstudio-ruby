import sys
import os
import glob as gb
import re
from conans import ConanFile, CMake
from conans.errors import ConanException, ConanInvalidConfiguration


class OpenstudiorubyConan(ConanFile):
    name = "openstudio_ruby"
    version = "2.5.5"
    license = "<Put the package license here>"  # TODO
    author = "NREL <openstudio@nrel.gov>"
    url = "https://github.com/NREL/conan-openstudio-ruby"
    description = "Static ruby for use in OpenStudio's Command Line Interface"
    topics = ("ruby", "openstudio")
    # THIS is what creates the package_id (sha) that will determine whether
    # we pull binaries from bintray or build them
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = "*"
    generators = "cmake"

    options = {
        'with_libyaml': [True, False],
        'with_libffi': [True, False],
        # GDBM depends on readline
        'with_gdbm': [True, False],
        # Readline doesn't work for MSVC currently
        'with_readline': [True, False],
        'with_gmp': [True, False],
    }
    default_options = {x: True for x in options}

    def configure(self):
        if ((self.settings.os == "Windows") and
           (self.settings.compiler == "Visual Studio")):
            self.output.warn(
                "Readline (hence GDBM) will not work on MSVC right now")
            self.options.with_gdbm = False
            self.options.with_readline = False
            self.output.warn(
                "Conan LIBFFI will not allow linking right now with MSVC, "
                "so temporarilly built it from CMakeLists instead")
            self.options.with_libffi = False
            self.output.info(
                "Conan LibYAML will not link properly right now with MSVC, "
                "so using built-in Psych provided libYAML")
            self.options.with_libyaml = False
            self.output.warn(
                "Conan GMP isn't supported on MSVC")
            self.options.with_gmp = False

        # I could let it slide, and hope for the best, but I'm afraid of other
        # incompatibilities, so just raise (which shouldn't happen when trying
        # to install from OpenStudio's cmake)
        if (self.settings.compiler == 'gcc'):
            if (self.settings.compiler.libcxx != "libstdc++11"):
                msg = ("This isn't meant to be compiled with an old "
                       " GCC ABI (though complation will work), "
                       "please use settings.compiler.libcxx=libstdc++11")
                raise ConanInvalidConfiguration(msg)

        # I delete the libcxx setting now, so that the package_id isn't
        # calculated taking this into account.
        # Note: on Mac we may want to ensure we get libc++/libstdc++ for
        # performance reasons
        # (not sure which will be default on OpenStudio's CMake),
        # but at least that doesn't have actual incompatibility
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        """
        Declare required dependencies
        """
        # 1.1.1x isn't supported by ruby 2.5.5, build fails
        self.requires("openssl/1.1.0l")
        self.requires("zlib/1.2.11")

        if self.options.with_libyaml:
            self.requires("libyaml/0.2.2@bincrafters/stable")
            self.options["libyaml"].shared = False
            # self.options["libyaml"].fPIC = True

        if self.options.with_libffi:
            self.requires("libffi/3.2.1")
            self.options["libffi"].shared = False
            # self.options["libffi"].fPIC = True

        if self.options.with_gdbm:
            self.requires("gdbm/1.18.1@bincrafters/stable")
            self.options["gdbm"].shared = False
            # self.options["gdbm"].fPIC = True
            self.options["gdbm"].libgdbm_compat = True

        if self.options.with_readline:
            self.requires("readline/7.0@bincrafters/stable")
            # self.options["readline"].shared = True
            # self.options["readline"].fPIC = True

        if self.options.with_gmp:
            self.requires("gmp/6.1.2")

    def build_requirements(self):
        """
        Build requirements are requirements that are only installed and used
        when the package is built from sources. If there is an existing
        pre-compiled binary, then the build requirements for this package will
        not be retrieved.
        """
        self.build_requires("ruby_installer/2.5.5@bincrafters/stable")
        self.build_requires("bison_installer/3.3.2@bincrafters/stable")

    def build(self):
        """
        This method is used to build the source code of the recipe using the
        CMakeLists.txt
        """
        cmake = CMake(self)
        cmake.definitions["INTEGRATED_CONAN"] = False
        cmake.configure()

        # On Windows the build never succeeds on the first try. Much effort
        # was spent trying to figure out why. This is the compromise:
        # we just build twice.
        if self.settings.os == "Windows":
            try:
                cmake.build()
            except:
                # total hack to allow second attempt at building
                self.should_build = True
                cmake.build()
        else:
            cmake.build()

    def package(self):
        """
        The actual creation of the package, once that it is built, is done
        here by copying artifacts from the build folder to the package folder
        """
        self.copy("*", src="Ruby-prefix/src/Ruby-install", keep_path=True)

    def _find_config_header(self):
        """
        Locate the ruby/config.h which will be in different folders depending
        on the platform

        eg:
            include/ruby-2.5.0/x64-mswin64_140
            include/ruby-2.5.0/x86_64-linux
            include/ruby-2.5.0/x86_64-darwin17
        """
        found = []

        # Glob recursive Works in python3.4 and above only...
        if sys.version_info > (3, 4):
            found = gb.glob("**/ruby/config.h", recursive=True)
        else:
            import fnmatch
            for root, dirnames, filenames in os.walk('.'):
                for filename in fnmatch.filter(filenames, 'config.h'):
                    if root.endswith('ruby'):
                        found.append(os.path.join(root, filename))

        if len(found) != 1:
            raise ConanException("Didn't find one and one only ruby/config.h")

        p = found[0]
        abspath = os.path.abspath(os.path.join(p, os.pardir, os.pardir))
        relpath = os.path.relpath(abspath, ".")
        # Add a success (in green) to ensure it did the right thing
        self.output.success("Found config.h in {}".format(relpath))
        return relpath

    def package_info(self):
        """
        Specify certain build information for consumers of the package
        Mostly we properly define libs to link against, libdirs and includedirs
        so that it can work with OpenStudio
        """
        # We'll glob for this extension
        if self.settings.os == "Windows":
            libext = "lib"
        else:
            libext = "a"

        # Note: If you don't specify explicitly self.package_folder, "."
        # actually already resolves to it when package_info is run

        # Glob all libraries, keeping only their name (and not the path)
        glob_pattern = "**/*.{}".format(libext)
        # glob_pattern = os.path.join(self.package_folder, glob_pattern)

        # Glob recursive Works in python3.4 and above only...
        libs = []
        if sys.version_info > (3, 4):
            libs = gb.glob(glob_pattern, recursive=True)
        else:
            import fnmatch
            for root, dirnames, filenames in os.walk('.'):
                for filename in fnmatch.filter(filenames,
                                               '*.{}'.format(libext)):
                    libs.append(os.path.join(root, filename))

        if not libs:
            # Add debug info
            self.output.info("cwd: {}".format(os.path.abspath(".")))
            self.output.info("Package folder: {}".format(self.package_folder))
            self.output.error("Globbing: {}".format(glob_pattern))
            raise ConanException("Didn't find the libraries!")

        # Remove the non-static VS libs
        if self.settings.os == "Windows":
            non_stat_re = re.compile(r'x64-vcruntime[0-9]+-ruby[0-9]+\.lib')
            exclude_libs = [x for x in libs
                            if non_stat_re.search(x)]
            if not exclude_libs:
                self.output.error("Did not find any static lib to exclude, "
                                  "expected at least one on Windows")
            else:
                print("Excluding {} non-static libs: "
                      "{}".format(len(exclude_libs), exclude_libs))

                # Now we actually exclude it
                libs = list(set(libs) - set(exclude_libs))

        # Relative to package folder: no need unless explicitly setting glob
        # to package_folder above
        # libs = [os.path.relpath(p, start=self.package_folder) for p in libs]

        # Keep only the names:
        self.cpp_info.libs = [os.path.basename(x) for x in libs]

        # These are the ext libs we expect on all platforms
        ext_libs = [
            'bigdecimal', 'bubblebabble', 'console', 'continuation',
            'coverage', 'cparse', 'date_core', 'digest', 'escape', 'etc',
            'fcntl', 'fiber', 'fiddle', 'generator', 'libenc', 'libtrans',
            'md5', 'nkf', 'nonblock', 'objspace', 'openssl', 'parser',
            'pathname', 'psych', 'ripper', 'rmd160', 'sdbm', 'sha1', 'sha2',
            'sizeof', 'socket', 'stringio', 'strscan', 'wait', 'zlib']

        if self.options.with_gdbm:
            ext_libs += ['dbm', 'gdbm']
        if self.options.with_readline:
            ext_libs += ['readline']

        # Not sure here...
        if self.settings.os == 'Windows':
            ext_libs += ['dltest', 'resolv']
        elif self.settings.os in ['Linux', 'Macos']:
            ext_libs += ['pty',
                         'syslog']

        # Now, append the lib extension, platform specific
        ext_libs = ['{}.{}'.format(libname, libext) for libname in ext_libs]

        if self.settings.os == 'Linux':
            expected_libs = ['libruby-static.a'] + ext_libs

        elif self.settings.os == 'Macos':
            expected_libs = (['libruby.{v}-static.a'.format(v=self.version)] +
                             ext_libs)

        elif self.settings.os == 'Windows':
            expected_libs = (['x64-vcruntime140-ruby250-static.lib'] +
                             ext_libs)

            expected_libs += ['at_exit-x64-mswin64_140.lib',
                              'bignum-x64-mswin64_140.lib',
                              'bug_3571-x64-mswin64_140.lib',
                              'bug_5832-x64-mswin64_140.lib',
                              'bug_reporter-x64-mswin64_140.lib',
                              'call_without_gvl-x64-mswin64_140.lib',
                              'class-x64-mswin64_140.lib',
                              'compat-x64-mswin64_140.lib',
                              'console-x64-mswin64_140.lib',
                              'debug-x64-mswin64_140.lib',
                              'dln-x64-mswin64_140.lib',
                              'dot.dot-x64-mswin64_140.lib',
                              'empty-x64-mswin64_140.lib',
                              'exception-x64-mswin64_140.lib',
                              'fd_setsize-x64-mswin64_140.lib',
                              'file-x64-mswin64_140.lib',
                              'float-x64-mswin64_140.lib',
                              'foreach-x64-mswin64_140.lib',
                              'funcall-x64-mswin64_140.lib',
                              'hash-x64-mswin64_140.lib',
                              'integer-x64-mswin64_140.lib',
                              'internal_ivar-x64-mswin64_140.lib',
                              'iseq_load-x64-mswin64_140.lib',
                              'iter-x64-mswin64_140.lib',
                              'memory_status-x64-mswin64_140.lib',
                              'method-x64-mswin64_140.lib',
                              'notimplement-x64-mswin64_140.lib',
                              'num2int-x64-mswin64_140.lib',
                              'numhash-x64-mswin64_140.lib',
                              'path_to_class-x64-mswin64_140.lib',
                              'postponed_job-x64-mswin64_140.lib',
                              'printf-x64-mswin64_140.lib',
                              'proc-x64-mswin64_140.lib',
                              'protect-x64-mswin64_140.lib',
                              'rational-x64-mswin64_140.lib',
                              'rb_fatal-x64-mswin64_140.lib',
                              'recursion-x64-mswin64_140.lib',
                              'regexp-x64-mswin64_140.lib',
                              'resize-x64-mswin64_140.lib',
                              'scan_args-x64-mswin64_140.lib',
                              'string-x64-mswin64_140.lib',
                              'struct-x64-mswin64_140.lib',
                              'symbol-x64-mswin64_140.lib',
                              'thread_fd_close-x64-mswin64_140.lib',
                              'time-x64-mswin64_140.lib',
                              'tracepoint-x64-mswin64_140.lib',
                              'typeddata-x64-mswin64_140.lib',
                              'update-x64-mswin64_140.lib',
                              'usr-x64-mswin64_140.lib',
                              'wait_for_single_fd-x64-mswin64_140.lib']


            self.output.warn(
                "Since we are building a custom libffi, we are packaging it, as it's required for linking our ruby")
            expected_libs += ['libffi.lib']

        n_libs = len(libs)
        n_expected_libs = len(expected_libs)
        if (n_libs == n_expected_libs):
            self.output.success("Found {} libs".format(n_libs))

        else:
            missing_libs = set(expected_libs) - set(libs)
            if missing_libs:
                self.output.error("Missing {} libraries: "
                                  "{}".format(len(missing_libs), missing_libs))

            extra_libs = set(libs) - set(expected_libs)
            if extra_libs:
                self.output.error("Found {} extra libraries: "
                                  "{}".format(len(extra_libs), extra_libs))

            self.output.error("Found {} libs, expected {} "
                              "libs".format(n_libs, n_expected_libs))

        # self.cpp_info.libdirs = ['lib', 'lib/ext', 'lib/enc']
        # Equivalent automatic detection
        # list of unique folders
        libdirs = list(set([os.path.dirname(x) for x in libs]))
        # Sort it by nesting level, smaller first
        libdirs.sort(key=lambda p: len(os.path.normpath(p).split(os.sep)))
        self.cpp_info.libdirs = libdirs

        self.cpp_info.includedirs = ['include', 'include/ruby-2.5.0']
        self.cpp_info.includedirs.append(self._find_config_header())

        self.output.info("cpp_info.libs = {}".format(self.cpp_info.libs))
        self.output.info("cpp_info.includedirs = "
                         "{}".format(self.cpp_info.includedirs))
