from conans import ConanFile, CMake, tools
from conans.tools import download, unzip
import os
import shutil


class FlannConan(ConanFile):
    name = "flann"
    version = "1.8.4"
    license = "BSD"
    url = "http://www.cs.ubc.ca/research/flann/"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"

    def source(self):
        self.run("git clone https://github.com/mariusmuja/flann flann-src")
        self.run("cd flann-src && git checkout %s"%(self.version))

        patch_file = 'patch-%s-%s.patch'%(self.version, self.settings.os)
        if os.path.exists(patch_file):
            tools.patch(patch_file=patch_file)

        # # Download source from an archive
        # zip_name = "flann-%s-src.zip"%self.version
        # download("http://www.cs.ubc.ca/research/flann/uploads/FLANN/flann-%s-src.zip"%self.version, zip_name)
        # unzip(zip_name)
        # shutil.move("flann-%s-src"%self.version, "flann")

    def build(self):
        cmake = CMake(self)
        args = ["-DBUILD_SHARED_LIBS=ON" if self.options.shared else ""]
        args += ['-DCMAKE_INSTALL_PREFIX="%s"' % self.package_folder]

        self.run('cmake flann %s %s'%(cmake.command_line, ' '.join(args)))
        self.run("cmake --build . --target install %s"%cmake.build_config)

    def package(self):
        pass

    def package_info(self):
        self.cpp_info.libs = []
