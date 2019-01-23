#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, shutil
from io import StringIO # Python 2 and 3 compatible
from conans import ConanFile, CMake, tools
from conans.model.version import Version


class FlannConan(ConanFile):
    name            = 'flann'
    version         = 'latest'
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

        if tools.os_info.is_windows:
            self.requires('lz4/[>=1.8.3]@ntc/binary')
        else:
            self.requires('lz4/[>=1.8.3]@ntc/stable')

    def source(self):
        g = tools.Git(folder='flann-src')
        g.clone('https://github.com/mariusmuja/flann.git', branch='master')

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
        pkg_config_vars = {}
        s = '\nBase Environment:\n'
        for k,v in os.environ.items():
            s += ' - %s=%s\n'%(k, v)
            if 'PKG_CONFIG' in k:
                pkg_config_vars[k] = v
        self.output.info(s)

        if len(pkg_config_vars):
            s = '\nPkg-Config Specific Environment:\n'
            for k,v in pkg_config_vars.items():
                if k != 'PKG_CONFIG_PATH':
                    s += ' - %s=%s\n'%(k, v)
            if 'PKG_CONFIG_PATH' in pkg_config_vars:
                s += ' - PKG_CONFIG_PATH:\n  - %s'%('\n  - '.join(pkg_config_vars['PKG_CONFIG_PATH'].split(';' if tools.os_info.is_windows else ':')))
            self.output.info(s)
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
