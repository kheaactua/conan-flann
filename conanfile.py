#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import os, re, shutil
from io import StringIO # Python 2 and 3 compatible
from conans import ConanFile, CMake, tools
from conans.model.version import Version


class FlannConan(ConanFile):
    name            = 'flann'
    license         = 'BSD'
    url             = 'http://www.cs.ubc.ca/research/flann/'
    description     = 'Fast Library for Approximate Nearest Neighbors'
    settings        = 'os', 'compiler', 'build_type', 'arch'
    options         = {
        'shared': [True, False],
        'fPIC':   [True, False],
        'cxx11':  [True, False],
    }
    default_options = 'shared=True', 'fPIC=True', 'cxx11=True'
    generators      = 'cmake'
    exports         = 'patch*'
    requires        = 'helpers/[>=0.3]@ntc/stable'

    def config_options(self):
        if 'Visual Studio' == self.settings.compiler:
            self.options.remove("fPIC")

    def requirements(self):
        if 'Visual Studio' == self.settings.compiler and Version(str(self.version)) <= '12':
            self.requires('gtest/1.8.0@bincrafters/stable')
        else:
            self.requires('gtest/[>=1.8.0]@bincrafters/stable')

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
            g = tools.Git('flann-src')
            g.clone('https://github.com/mariusmuja/flann', branch=self.version)

        patch_file = f'patch-{self.version}-{self.settings.os}.patch'
        if os.path.exists(patch_file):
            tools.patch(patch_file=patch_file, base_path='flann-src')

        self.fix_cmake_311_issue()

        if 'gcc' == self.settings.compiler:
            import cmake_helpers
            cmake_helpers.wrapCMakeFile(os.path.join(self.source_folder, 'flann-src'), output_func=self.output.info)

    def fix_cmake_311_issue(self):
        """ add_library(name TYPE "") is no longer valid as of CMake >=3.11 """

        mybuf = StringIO()
        self.run('cmake --version', output=mybuf)
        outp = mybuf.getvalue()
        m1 = re.match(r'cmake version (?P<version>\d+\.\d+.\d+).*', outp)
        if m1:
            if Version(str(m1.group('version'))) > '3.11':
                with open(os.path.join(self.source_folder, 'flann-src', 'src', 'cpp', 'empty.cpp'), 'w') as f:
                    f.write('/* empty */')
                with open(os.path.join(self.source_folder, 'flann-src', 'src', 'cpp', 'CMakeLists.txt'), 'r') as f: data = f.read()
                data = data.replace('add_library(flann_cpp SHARED "")', 'add_library(flann_cpp SHARED "empty.cpp")')
                data = data.replace('add_library(flann SHARED "")', 'add_library(flann SHARED "empty.cpp")')
                with open(os.path.join(self.source_folder, 'flann-src', 'src', 'cpp', 'CMakeLists.txt'), 'w') as f:
                    f.write(data)
        else:
            self.info.error('Could not detect CMake version')

    def setup_cmake(self):

        cmake = CMake(self)

        cmake.definitions['BUILD_SHARED_LIBS:BOOL'] = 'TRUE' if self.options.shared else 'FALSE'
        cmake.definitions['GTEST_ROOT:PATH'] = self.deps_cpp_info['gtest'].rootpath

        if 'fPIC' in self.options and self.options.fPIC:
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = 'ON'

        # Not sure this has any impact in flann
        if self.options.cxx11:
            cmake.definitions['CMAKE_CXX_STANDARD'] = 11

        if 'gcc' == self.settings.compiler:
            cmake.definitions['ADDITIONAL_CXX_FLAGS:STRING'] = '-frecord-gcc-switches'

        return cmake

    def build(self):
        cmake = self.setup_cmake()

        # Debug
        s = '\nCMake Definitions:\n'
        for k,v in cmake.definitions.items():
            s += ' - %s=%s\n'%(k, v)
        self.output.info(s)

        cmake.configure(source_folder='flann-src')
        cmake.build()

    def package(self):
        cmake = self.setup_cmake()
        cmake.configure(source_folder='flann-src')
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        # Populate the pkg-config environment variables
        with tools.pythonpath(self):
            from platform_helpers import adjustPath, appendPkgConfigPath
            self.env_info.PKG_CONFIG_FLANN_PREFIX = adjustPath(self.package_folder)
            appendPkgConfigPath(adjustPath(os.path.join(self.package_folder, 'lib', 'pkgconfig')), self.env_info)

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
