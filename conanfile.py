from conans import ConanFile, CMake, tools


class OpenstudiorubyConan(ConanFile):
    name = "openstudio-ruby"
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

    def package_info(self):
        self.cpp_info.libs = ['libruby-static.a', "pathname.a", "objspace.a", "readline.a", "zlib.a", "sizeof.a", "strscan.a", "parser.a", "fiber.a", "cparse.a", "wait.a", "fcntl.a", "coverage.a", "stringio.a", "generator.a", "nonblock.a", "psych.a", "socket.a", "pty.a", "etc.a", "dbm.a", "fiddle.a", 'sha2.a', "syslog.a", "sdbm.a", "digest.a", "bigdecimal.a", "console.a", "bubblebabble.a", "ripper.a", 'date_core.a', "nkf.a", "gdbm.a", 'rmd160.a', "continuation.a", "openssl.a", 'sha1.a', 'md5.a', "escape.a", "libtrans.a", "libenc.a"]
        
        self.cpp_info.libdirs = ['lib', 'lib/ext', 'lib/enc']
        self.cpp_info.includedirs = ['include', 'include/ruby-2.5.0', 'include/ruby-2.5.0/x86_64-linux']

