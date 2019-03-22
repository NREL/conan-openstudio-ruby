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
    generators = "cmake"


    def configure(self):
        self.requires("OpenSSL/1.1.0g@conan/stable")
        self.requires("ruby_installer/2.5.1@bincrafters/stable")
        self.requires("zlib/1.2.11@conan/stable")



    def build(self):
        cmake = CMake(self)
        cmake.definitions["INTEGRATED_CONAN"] = False
        cmake.configure()
        cmake.build()


    def package(self):
        self.copy("*.h", dst="include", src="hello")
        self.copy("*hello.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["hello"]

