import os, shutil
from conans import ConanFile, CMake, tools


class FlannConan(ConanFile):
    name            = "flann"
    version         = "1.8.4"
    # version         = "1.9.1"
    license         = "BSD"
    url             = "http://www.cs.ubc.ca/research/flann/"
    settings        = "os", "compiler", "build_type", "arch"
    options         = {"shared": [True, False]}
    default_options = "shared=True"
    generators      = "cmake"
    exports         = "patch*"

    def source(self):
        hashes = {
            '1.8.4': '774b74580e3cbc5b0d45c6ec345a64ae',
            '1.9.1': '73adef1c7bf8e8b978987e7860926ea6',
        }

        if self.version in hashes:
            archive = f'{self.version}.tar.gz'
            tools.download(
                url=f'https://github.com/mariusmuja/flann/archive/{archive}',
                filename=archive
            )
            tools.check_md5(archive, hashes[self.version])
            tools.unzip(archive)
            shutil.move(f'flann-{self.version}', 'flann-src')
        else:
            self.run("git clone https://github.com/mariusmuja/flann flann-src")
            self.run("cd flann-src && git checkout %s"%(self.version))

        patch_file = f'patch-{self.version}-{self.settings.os}.patch'
        if os.path.exists(patch_file):
            tools.patch(patch_file=patch_file, base_path='flann-src')

    def build(self):

        args  = []
        args.append('-DBUILD_SHARED_LIBS:BOOL=%s'%('TRUE' if self.options.shared else 'FALSE'))

        cmake = CMake(self)
        cmake.configure(source_folder='flann-src')
        cmake.build()
        cmake.install()

    def package(self):
        pass

    def package_info(self):
        pass
