import os, shutil
from conans import ConanFile, CMake, tools


class FlannConan(ConanFile):
    name            = 'flann'
    license         = 'BSD'
    url             = 'http://www.cs.ubc.ca/research/flann/'
    settings        = 'os', 'compiler', 'build_type', 'arch'
    options         = {
        'shared': [True, False],
        'fPIC':   [True, False],
        'cxx11':  [True, False],
    }
    default_options = 'shared=True', 'fPIC=True', 'cxx11=True'
    generators      = 'cmake'
    exports         = 'patch*'
    requires = 'gtest/[>=1.8.0]@lasote/stable', 'helpers/[>=0.1]@ntc/stable'

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

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
            self.run('git clone https://github.com/mariusmuja/flann flann-src')
            self.run(f'cd flann-src && git checkout {self.version}')

        patch_file = f'patch-{self.version}-{self.settings.os}.patch'
        if os.path.exists(patch_file):
            tools.patch(patch_file=patch_file, base_path='flann-src')

        if self.settings.compiler == 'gcc':
            import cmake_helpers
            cmake_helpers.wrapCMakeFile(os.path.join(self.source_folder, 'flann-src'), output_func=self.output.info)

    def build(self):
        cmake = CMake(self)

        cmake.definitions['BUILD_SHARED_LIBS:BOOL'] = 'TRUE' if self.options.shared else 'FALSE'
        cmake.definitions['GTEST_ROOT:PATH'] = self.deps_cpp_info['gtest'].rootpath

        if 'fPIC' in self.options and self.options.fPIC:
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = 'ON'

        # Not sure this has any impact in flann
        if self.options.cxx11:
            cmake.definitions['CMAKE_CXX_STANDARD'] = 11

        if self.settings.compiler == 'gcc':
            cmake.definitions['ADDITIONAL_CXX_FLAGS:STRING'] = '-frecord-gcc-switches'

        # Debug
        s = '\nCMake Definitions:\n'
        for k,v in cmake.definitions.items():
            s += ' - %s=%s\n'%(k, v)
        self.output.info(s)

        cmake.configure(source_folder='flann-src')
        cmake.build()
        cmake.install()

    def package(self):
        pass

    def package_info(self):
        libs = ['flann', 'flann_cpp_s', 'flann_s']
        if 'Linux' == self.settings.os:
            prefix = 'lib'
            suffix = 'so' if self.options.shared else 'a'
        else:
            prefix = ''
            suffix = 'lib'

        self.cpp_info.libs += list(map(lambda lib: f'{prefix}{lib}.{suffix}', libs))

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
