import os
import glob as gb
from conans import ConanFile, CMake, tools


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
        print("Found config.h in {}".format(relpath))
        return relpath

    def package_info(self):
        # TODO: This can certainly be done better with file globbing
        # or something

        if self.settings.os == "Windows":
            # self.cpp_info.libs = ['x64-vcruntime140-ruby250-static.lib',
            #                       "at_exit-x64-mswin64_140.lib",
            #                       "bigdecimal.lib",
            #                       "bignum-x64-mswin64_140.lib",
            #                       "bubblebabble.lib",
            #                       "bug_3571-x64-mswin64_140.lib",
            #                       "bug_5832-x64-mswin64_140.lib",
            #                       "bug_reporter-x64-mswin64_140.lib",
            #                       "call_without_gvl-x64-mswin64_140.lib",
            #                       "class-x64-mswin64_140.lib",
            #                       "compat-x64-mswin64_140.lib",
            #                       "console.lib",
            #                       "console-x64-mswin64_140.lib",
            #                       "continuation.lib",
            #                       "coverage.lib",
            #                       "cparse.lib",
            #                       "date_core.lib",
            #                       "debug-x64-mswin64_140.lib",
            #                       "digest.lib",
            #                       "dlntest.lib",
            #                       "dln-x64-mswin64_140.lib",
            #                       "dot.dot-x64-mswin64_140.lib",
            #                       "empty-x64-mswin64_140.lib",
            #                       "escape.lib",
            #                       "etc.lib",
            #                       "exception-x64-mswin64_140.lib",
            #                       "fcntl.lib",
            #                       "fd_setsize-x64-mswin64_140.lib",
            #                       "fiber.lib",
            #                       "fiddle.lib",
            #                       "file-x64-mswin64_140.lib",
            #                       "float-x64-mswin64_140.lib",
            #                       "foreach-x64-mswin64_140.lib",
            #                       "funcall-x64-mswin64_140.lib",
            #                       "generator.lib",
            #                       "hash-x64-mswin64_140.lib",
            #                       "integer-x64-mswin64_140.lib",
            #                       "internal_ivar-x64-mswin64_140.lib",
            #                       "iseq_load-x64-mswin64_140.lib",
            #                       "iter-x64-mswin64_140.lib",
            #                       "md5.lib",
            #                       "memory_status-x64-mswin64_140.lib",
            #                       "method-x64-mswin64_140.lib",
            #                       "nkf.lib",
            #                       "nonblock.lib",
            #                       "notimplement-x64-mswin64_140.lib",
            #                       "num2int-x64-mswin64_140.lib",
            #                       "numhash-x64-mswin64_140.lib",
            #                       "objspace.lib",
            #                       "openssl.lib",
            #                       "parser.lib",
            #                       "path_to_class-x64-mswin64_140.lib",
            #                       "pathname.lib",
            #                       "postponed_job-x64-mswin64_140.lib",
            #                       "printf-x64-mswin64_140.lib",
            #                       "proc-x64-mswin64_140.lib",
            #                       "protect-x64-mswin64_140.lib",
            #                       "psych.lib",
            #                       "rational-x64-mswin64_140.lib",
            #                       "rb_fatal-x64-mswin64_140.lib",
            #                       "recursion-x64-mswin64_140.lib",
            #                       "regexp-x64-mswin64_140.lib",
            #                       "resize-x64-mswin64_140.lib",
            #                       "resolv.lib",
            #                       "ripper.lib",
            #                       "rmd160.lib",
            #                       "scan_args-x64-mswin64_140.lib",
            #                       "sdbm.lib",
            #                       "sha1.lib",
            #                       "sha2.lib",
            #                       "sizeof.lib",
            #                       "socket.lib",
            #                       "stringio.lib",
            #                       "string-x64-mswin64_140.lib",
            #                       "strscan.lib",
            #                       "struct-x64-mswin64_140.lib",
            #                       "symbol-x64-mswin64_140.lib",
            #                       "thread_fd_close-x64-mswin64_140.lib",
            #                       "time-x64-mswin64_140.lib",
            #                       "tracepoint-x64-mswin64_140.lib",
            #                       "typeddata-x64-mswin64_140.lib",
            #                       "update-x64-mswin64_140.lib",
            #                       "usr-x64-mswin64_140.lib",
            #                       "wait.lib",
            #                       "wait_for_single_fd-x64-mswin64_140.lib",
            #                       "zlib.lib",
            #                       "libtrans.lib",
            #                       "libenc.lib"]

            libext = "lib"

        else:

            # self.cpp_info.libs = ['libruby-static.a', "pathname.a",
            #                       "objspace.a", "readline.a", "zlib.a",
            #                       "sizeof.a", "strscan.a", "parser.a",
            #                       "fiber.a", "cparse.a", "wait.a", "fcntl.a",
            #                       "coverage.a", "stringio.a", "generator.a",
            #                       "nonblock.a", "psych.a", "socket.a",
            #                       "pty.a", "etc.a", "dbm.a", "fiddle.a",
            #                       'sha2.a', "syslog.a", "sdbm.a", "digest.a",
            #                       "bigdecimal.a", "console.a",
            #                       "bubblebabble.a", "ripper.a", 'date_core.a',
            #                       "nkf.a", "gdbm.a", 'rmd160.a',
            #                       "continuation.a", "openssl.a", 'sha1.a',
            #                       'md5.a', "escape.a", "libtrans.a",
            #                       "libenc.a"]

            libext = ".a"


        self.cpp_info.libs = libs = [os.path.basename(x) for x
                                     in gb.glob("**/*.{}".format(libext),
                                                recursive=True)]

        # include/ruby-2.5.0/x64-mswin64_140'
        # 'include/ruby-2.5.0/x86_64-linux',
        # 'include/ruby-2.5.0/x86_64-darwin17'
        self.cpp_info.libdirs = ['lib', 'lib/ext', 'lib/enc']
        self.cpp_info.includedirs = ['include', 'include/ruby-2.5.0']
        self.cpp_info.includedirs.append(self.find_config_header())

