from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rm, rmdir
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
import os


required_conan_version = ">=2.0.9"

class MsclConan(ConanFile):
    name = "mscl"
    description = "MicroStrain Communication Library"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.microstrain.com/software/mscl"
    topics = ("navigation", "sensors", "inertial-sensors", "microstrain")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ssl": [True, False],
        "with_websockets": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssl": True,
        "with_websockets": True,
    }
    implements = ["auto_shared_fpic"]

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/[>=1.68 <1.73]")
        if self.options.with_ssl:
            self.requires("openssl/[>=1.1 <4]")
        

    def validate(self):
        check_min_cppstd(self, 11)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["WITH_SSL"] = self.options.with_ssl
        tc.cache_variables["WITH_WEBSOCKETS"] = self.options.with_websockets
        tc.cache_variables["Boost_REQUESTED_VERSION"] = str(self.dependencies["boost"]).split("/")[1]
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        if self.options.shared:
            baseOutputDir = os.path.join(self.source_folder, "Output/C++/Shared")
        else:
            baseOutputDir = os.path.join(self.source_folder, "Output/C++/Static")
        libDir = os.path.join(baseOutputDir, "lib/")

        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        copy(self, "**", os.path.join(baseOutputDir, "MSCL/include"), os.path.join(self.package_folder, "include"))
        copy(self, "MSCL.lib", os.path.join(), os.path.join(self.package_folder, "lib"))
        if self.options.shared:
            pass # TODO: Copy DLL

    def package_info(self):
        self.cpp_info.libs = ["MSCL"]
        self.cpp_info.includedirs = [os.path.join(self.package_folder, "include")]
        self.cpp_info.libdirs = [os.path.join(self.package_folder, "lib")]
