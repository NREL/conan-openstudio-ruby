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
    options = {"shared": [True, False]}
    default_options = "shared=False"
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


