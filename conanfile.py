from conans import ConanFile, CMake, tools
from conans.tools import patch # Add unzip, and download  to use a zip file
import os
import shutil

import inspect

class FlannConan(ConanFile):
    name            = "flann"
    version         = "1.8.4"
    license         = "BSD"
    url             = "http://www.cs.ubc.ca/research/flann/"
    settings        = "os", "compiler", "build_type", "arch"
    options         = {"shared": [True, False]}
    default_options = "shared=True"
    generators      = "cmake"
    exports         = "patch*"

    def source(self):
        self.run("git clone https://github.com/mariusmuja/flann flann-src")
        self.run("cd flann-src && git checkout %s"%(self.version))

        patch_file = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'patch-%s-%s.patch'%(self.version, self.settings.os))
        if os.path.exists(patch_file):
            # Couldn't get tools.patch to work, maybe because the file was
            # generated in git?  Or maybe it's one directory off?
            # tools.patch(patch_file=patch_file)
            self.run("cd flann-src && git apply %s"%(patch_file))

        # # Download source from an archive
        # zip_name = "flann-%s-src.zip"%self.version
        # download("http://www.cs.ubc.ca/research/flann/uploads/FLANN/flann-%s-src.zip"%self.version, zip_name)
        # unzip(zip_name)
        # shutil.move("flann-%s-src"%self.version, "flann-src")

    def build(self):
        cmake = CMake(self)
        args  = []
        args.append("-DBUILD_SHARED_LIBS=ON" if self.options.shared else "")
        args.append('-DCMAKE_INSTALL_PREFIX="%s"'%self.package_folder)

        self.run('cmake flann-src %s %s'%(cmake.command_line, ' '.join(args)))
        self.run("cmake --build . --target install %s"%cmake.build_config)

    def package(self):
        pass

    def package_info(self):
        self.cpp_info.libs = []
