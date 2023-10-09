from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.build import check_min_cppstd
from conan.tools.files import get, copy, replace_in_file
from conan.errors import ConanInvalidConfiguration

import os.path

class NanaConan(ConanFile):
    name = "nana"
    license = "BSL-1.0"
    url = "http://nanapro.org/"
    description = "Nana is a cross-platform library for GUI programming in modern C++ style"
    topics = ("gui", "ui", "forms", "user", "interface", "modern")

    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_audio": [True, False],
        "enable_jpeg": [True, False],
        "enable_png": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "enable_audio": False,
        "enable_jpeg": False,
        "enable_png": False,
    }

    def source(self):
        get(
            self,
            **self.conan_data["sources"][self.version],
            destination=self.source_folder,
            strip_root=True,
        )

    def validate(self):
        check_min_cppstd(self, "11")

        # There is some odd issue with dll's cmake and windows
        if self.options.shared and self.settings.os == "Windows":
            raise ConanInvalidConfiguration("Shared lib on windows is currently broken!")

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("xorg/system")
            self.requires("libxft/2.3.6")
            self.requires("freetype/2.13.0")

            if self.options.enable_audio:
                raise ConanInvalidConfiguration("enable_audio is currently not supported on linux!")

        if self.options.enable_jpeg:
            self.requires("libjpeg/9e")
        if self.options.enable_png:
            self.requires("libpng/1.6.39")

    def build_requirements(self):
        self.build_requires("cmake/3.26.4")
        if self.settings.os == "Linux":
            self.tool_requires("pkgconf/1.9.3")

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)

        # Enable the use of the conan configuration header
        # (required for all following options)
        tc.variables["NANA_CMAKE_ENABLE_CONF"] = True
        # Use os like include paths (but the libs will be provided by conan)
        tc.variables["NANA_CMAKE_LIBJPEG_FROM_OS"] = True
        tc.variables["NANA_CMAKE_LIBPNG_FROM_OS"] = True
        # Make cmake install work
        tc.variables["NANA_CMAKE_INSTALL"] = True

        # Set vars for optional features
        tc.variables["NANA_CMAKE_ENABLE_AUDIO"] = self.options.enable_audio
        tc.variables["NANA_CMAKE_ENABLE_JPEG"] = self.options.enable_jpeg
        tc.variables["NANA_CMAKE_ENABLE_PNG"] = self.options.enable_png

        # Static runtime for msvc
        compiler = self.settings.get_safe("compiler")
        if compiler and str(compiler).lower() == "msvc":
            compiler_runtime = self.settings.get_safe("compiler.runtime")
            tc.variables["MSVC_USE_STATIC_RUNTIME"] = (
                compiler_runtime != None and (compiler_runtime).lower() == "static"
                )

        tc.generate()

    def build(self):
        # We need to patch "system/split_string.cpp" on old versions
        # they used "and" instead of "&&" in this file
        # TODO: Create a proper patch
        if self.version == "1.7.4":
            replace_in_file(
                self, 
                os.path.join(self.source_folder, "source/system", "split_string.cpp"),
                " and ", " && "
                )

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.libs = ["nana"]

        # Add defines based on options
        if self.options.enable_audio:
            self.cpp_info.defines.append("NANA_ENABLE_AUDIO")
        if self.options.enable_jpeg:
            self.cpp_info.defines.extend(("NANA_ENABLE_JPEG", "USE_LIBJPEG_FROM_OS"))
        if self.options.enable_png:
            self.cpp_info.defines.extend(("NANA_ENABLE_PNG", "USE_LIBPNG_FROM_OS"))
