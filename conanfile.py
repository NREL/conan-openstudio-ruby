import sys
import os
import glob as gb
import re
from conans import ConanFile, CMake, tools
from conans.errors import ConanException, ConanInvalidConfiguration


class OpenstudiorubyConan(ConanFile):
    name = "openstudio_ruby"
    version = "3.1.3"
    license = "<Put the package license here>"  # TODO
    author = "NREL <openstudio@nrel.gov>"
    url = "https://github.com/NREL/conan-openstudio-ruby"
    description = "Static ruby for use in OpenStudio's Command Line Interface"
    topics = ("ruby", "openstudio")
    # THIS is what creates the package_id (sha) that will determine whether
    # we pull binaries from bintray or build them
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = ["CMakeLists.txt", "patches/*", "!patches/unused/*"
                       "*.bat", "*.bat.in", "test_openssl_version.rb"]
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

    @property
    def _is_msvc(self):
        # conan raises an exception if you compare a setting with a value
        # which is not listed in settings.yml (`msvc` added in 1.40.0)
        # so use `str` for now...
        return str(self.settings.compiler) in ['Visual Studio', 'msvc']

    def configure(self):
        if (self.settings.os == "Windows"):
            self.output.warn(
                "Readline (hence GDBM) will not work on Windows right now")
            self.options.with_gdbm = False
            # TODO: vcpkg supports readline, see https://github.com/ruby/ruby/blob/1b377b32c8616f85c0a97e68758c5c2db83f2169/.github/workflows/windows.yml#L28
            # But conan readline doesn't support msvc
            self.options.with_readline = False

        if self._is_msvc:
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
        if tools.os_info.linux_distro not in ["centos"]:
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
        # Doesn't work with 3.x.
        # Doesn't work on gcc 7 and 8 with 1.1.1n: had to patch it
        self.requires("openssl/1.1.1o")
        self.requires("zlib/1.2.12")

        if self.options.with_libyaml:
            self.requires("libyaml/0.2.5")
            # self.options["libyaml"].shared = False
            # self.options["libyaml"].fPIC = True

        if self.options.with_libffi:
            self.requires("libffi/3.4.2")
            # self.options["libffi"].shared = False
            # self.options["libffi"].fPIC = True

        if self.options.with_gdbm:
            self.requires("gdbm/1.19")
            # self.options["gdbm"].shared = False
            # self.options["gdbm"].fPIC = True
            self.options["gdbm"].libgdbm_compat = True
            self.options["gdbm"].with_libiconv = False
            self.options["gdbm"].with_nls = False
            if self.options.with_readline:
                self.options["gdbm"].with_readline = True

        if self.options.with_readline:
            self.requires("readline/8.1.2")
            # self.options["readline"].shared = True
            # self.options["readline"].fPIC = True

        if self.options.with_gmp:
            self.requires("gmp/6.2.1")

    def build_requirements(self):
        """
        Build requirements are requirements that are only installed and used
        when the package is built from sources. If there is an existing
        pre-compiled binary, then the build requirements for this package will
        not be retrieved.
        """
        if (self.settings.os == "Linux"):
            # Mac has it. Windows too. the conanio/gcc images do not
            self.build_requires("ruby_installer/2.7.3@nrel/stable")

        # cant use bison/3.5.3 from CCI as it uses m4 which won't build
        # with x86. So use bincrafters' still but explicitly add bin dir
        # to PATH later in CMakeLists.txt
        # self.build_requires("bison/3.5.3")
        # TODO: once https://github.com/conan-io/conan-center-index/pull/2250
        # is merged, revisit this. Edit: PR merged but still another problem...
        # Pending https://github.com/conan-io/conan-center-index/pull/2298
        # I'm using a special CONAN_BUILD_REQUIRES env var for win x86
        # self.build_requires("bison_installer/3.3.2@bincrafters/stable")
        # Yet it still doesn't work, since bison ITSELF has a problem with x86
        # names
        # if self.settings.os == "Windows" and self.settings.arch == 'x86':
        #     self.build_requires("bison_installer/3.3.2@bincrafters/stable")
        # else:

        # You CANNOT use bison 3.7.1 as it's stricter and will throw
        # redefinition errors in Ruby' parser.c
        # Latest bison with m4/1.4.18
        # self.build_requires("bison/3.7.1#dcffa3dd9204cb79ac7ca09a7f19bb8b")
        self.build_requires("bison/3.7.6")

    def build(self):
        """
        This method is used to build the source code of the recipe using the
        CMakeLists.txt
        """

        # Patching done in CMakeLists.txt for now
        # for patch in self.conan_data["patches"][self.version]:
        #     tools.patch(**patch)

        parallel = True
        if tools.os_info.linux_distro in ["centos"]:
            # parallel=False required or MFLAGS = -s --jobserver-fds=3,4 -j
            # is strapped and centos' make is too old to understand
            parallel = False

        cmake = CMake(self, parallel=parallel)
        cmake.definitions["OPENSSL_VERSION"] = self.deps_cpp_info["openssl"].version
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
            include/ruby-3.1.0/x64-mswin64_140
            include/ruby-3.1.0/i386-mswin32_140
            include/ruby-3.1.0/x86_64-linux
            include/ruby-3.1.0/x86_64-darwin17
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
            non_stat_re = re.compile(r'(x64-)?vcruntime[0-9]+-ruby[0-9]+\.lib')
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
        libnames = [os.path.basename(x) for x in libs]
        self.cpp_info.libs = libnames

        # These are the ext libs we expect on all platforms
        ext_libs = [
            'bigdecimal', 'bubblebabble', 'console', 'continuation',
            'coverage', 'cparse', 'date_core', 'digest', 'escape', 'etc',
            'fcntl', 'fiber', 'fiddle', 'generator', 'libenc', 'libtrans',
            'md5', 'nkf', 'nonblock', 'objspace', 'openssl', 'parser',
            'pathname', 'psych', 'ripper', 'rmd160', 'sdbm', 'sha1', 'sha2',
            'sizeof', 'socket', 'stringio', 'strscan', 'wait', 'zlib',
            # Didn't exist in 2.5.5
            'monitor',
        ]

        if self.options.with_gdbm:
            ext_libs += ['dbm', 'gdbm']
        if self.options.with_readline:
            ext_libs += ['readline']

        # Not sure here...
        if self.settings.os == 'Windows':
            ext_libs += ['dlntest', 'resolv',
                         # Using the included libffi
                         'libffi_convenience',
                         # Now with win32ole
                         'win32ole']
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
            # bignum-i386-mswin32_140.lib
            # bignum-x64-mswin64_140.lib
            if self.settings.arch == "x86":
                libarch = "i386-mswin32_140"
                expected_libs = (['vcruntime140-ruby270-static.lib'] +
                                 ext_libs)
            else:
                libarch = "x64-mswin64_140"
                expected_libs = (['x64-vcruntime140-ruby270-static.lib'] +
                                 ext_libs)

            expected_libs += ['at_exit-{l}.lib',
                              'bignum-{l}.lib',
                              'bug_3571-{l}.lib',
                              'bug_5832-{l}.lib',
                              'bug_14834-{l}.lib',
                              'bug_reporter-{l}.lib',
                              'call_without_gvl-{l}.lib',
                              'class-{l}.lib',
                              'compat-{l}.lib',
                              'console-{l}.lib',
                              'cxxanyargs-{l}.lib',
                              'debug-{l}.lib',
                              'dln-{l}.lib',
                              'dot.dot-{l}.lib',
                              'empty-{l}.lib',
                              'enumerator_kw-{l}.lib',
                              'exception-{l}.lib',
                              'extract-{l}.lib',
                              'fd_setsize-{l}.lib',
                              'file-{l}.lib',
                              'float-{l}.lib',
                              'foreach-{l}.lib',
                              'funcall-{l}.lib',
                              'hash-{l}.lib',
                              'integer-{l}.lib',
                              'internal_ivar-{l}.lib',
                              'iseq_load-{l}.lib',
                              'iter-{l}.lib',
                              'memory_status-{l}.lib',
                              'method-{l}.lib',
                              'notimplement-{l}.lib',
                              'num2int-{l}.lib',
                              'numhash-{l}.lib',
                              'path_to_class-{l}.lib',
                              'postponed_job-{l}.lib',
                              'printf-{l}.lib',
                              'proc-{l}.lib',
                              'protect-{l}.lib',
                              'rational-{l}.lib',
                              'rb_call_super_kw-{l}.lib',
                              'rb_fatal-{l}.lib',
                              'recursion-{l}.lib',
                              'regexp-{l}.lib',
                              'resize-{l}.lib',
                              'scan_args-{l}.lib',
                              'string-{l}.lib',
                              'struct-{l}.lib',
                              'symbol-{l}.lib',
                              'thread_fd_close-{l}.lib',
                              'time-{l}.lib',
                              'tracepoint-{l}.lib',
                              'typeddata-{l}.lib',
                              'update-{l}.lib',
                              'usr-{l}.lib',
                              'wait_for_single_fd-{l}.lib']
            expected_libs = [x.format(l=libarch) for x in expected_libs]



        n_libs = len(libnames)
        n_expected_libs = len(expected_libs)
        if (n_libs == n_expected_libs):
            self.output.success("Found {} libs".format(n_libs))

        else:
            missing_libs = set(expected_libs) - set(libnames)
            if missing_libs:
                self.output.error("Missing {} libraries: "
                                  "{}".format(len(missing_libs), missing_libs))

            extra_libs = set(libnames) - set(expected_libs)
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

        self.cpp_info.includedirs = ['include', 'include/ruby-2.7.0']
        self.cpp_info.includedirs.append(self._find_config_header())

        self.output.info("cpp_info.libs = {}".format(self.cpp_info.libs))
        self.output.info("cpp_info.libdirs = {}".format(self.cpp_info.libdirs))
        self.output.info("cpp_info.includedirs = "
                         "{}".format(self.cpp_info.includedirs))
