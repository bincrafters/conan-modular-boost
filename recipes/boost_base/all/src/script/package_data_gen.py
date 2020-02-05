#!/usr/bin/env python3
"""
    Copyright (C) 2018-2019 Rene Rivera.
    Use, modification and distribution are subject to the
    Boost Software License, Version 1.0. (See accompanying file
    LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
"""
import os.path
from bls.git_tool import Git
from bls.util import Main, PushDir
from bls.lib_data import LibraryData


script_dir = os.path.dirname(os.path.realpath(__file__))


class PackageGen(Main):
    '''
    Generates Boost packages for a release.
    '''

    def __init_parser__(self, parser):
        default_bin_dir = os.path.join(
            os.path.dirname(os.path.dirname(script_dir)),
            'build')
        default_out_dir = os.path.join(
            os.path.dirname(script_dir),
            'data')
        parser.add_argument(
            '++version',
            help='The version of Boost to generate packages for.')
        parser.add_argument(
            '++out-dir',
            help='Root directory to output the generated packages.',
            default=default_out_dir)
        parser.add_argument('++bin-dir', default=default_bin_dir)
        parser.add_argument('++local', action='store_true')
        parser.add_argument('++build-data', action='store_true')

    def __run__(self):
        bin_dir = None
        boost_root_dir = None
        data_dir = None

        with PushDir(self.args.bin_dir) as dir:
            bin_dir = dir
            boost_root_dir = os.path.join(bin_dir, 'boost_root')
        with PushDir(bin_dir, 'data') as dir:
            data_dir = dir

        with PushDir('.'):
            build_b2_py = os.path.join(script_dir, 'build_b2.py')
            build_bdep_py = os.path.join(script_dir, 'build_boostdep.py')
            clone_boost_py = os.path.join(script_dir, 'clone_boost.py')
            gen_lib_deps_py = os.path.join(script_dir, 'gen_lib_deps.py')
            gen_lib_ranks_py = os.path.join(script_dir, 'gen_lib_ranks.py')
            git_switch_py = os.path.join(script_dir, 'git_switch.py')

            # b2_exe = os.path.join(bin_dir, 'b2_root', 'bin', 'b2')

            rebuild_tools = os.environ.get(
                'CI', False) and self.args.build_data

            if not self.args.local:
                self.__check_call__([
                    clone_boost_py,
                    '++root=%s' % (boost_root_dir), '++trace'
                ])
            self.__check_call__([
                git_switch_py,
                '++root=%s' % (boost_root_dir), '++branch=develop', '++trace'
            ])
            tool_build_args = [
                '++boost-root=%s' % (boost_root_dir),
                '++bin=%s' % (bin_dir)
            ]
            if rebuild_tools:
                tool_build_args.append('++rebuild')
            self.__check_call__([build_b2_py] + tool_build_args)
            self.__check_call__([build_bdep_py] + tool_build_args)

            def gen_lib_data(branch=None, tag=None, rebuild=False):
                label = branch if branch else tag
                print('[GEN LIB DATA %s]' % (label))
                deps_file = os.path.join(data_dir, '%s-deps.json' % (label))
                ranks_headers_file = os.path.join(
                    data_dir, '%s-ranks-headers.json' % (label))
                ranks_build_file = os.path.join(
                    data_dir, '%s-ranks-build.json' % (label))
                if rebuild or not os.path.exists(deps_file):
                    self.__check_call__([
                        git_switch_py,
                        '++root=%s' % (boost_root_dir),
                        '++branch=%s' % (branch)
                        if branch else '++tag=%s' % (tag)
                    ])
                    self.__check_call__([
                        gen_lib_deps_py,
                        '++boost-root=%s' % (boost_root_dir),
                        '++json=%s' % (deps_file),
                        '++boostdep=%s' % (os.path.join(bin_dir, 'boostdep'))
                    ])
                    self.__check_call__([
                        gen_lib_ranks_py,
                        '++lib-info=%s' % (deps_file),
                        '++json=%s' % (ranks_headers_file)
                    ])
                    self.__check_call__([
                        gen_lib_ranks_py,
                        '++lib-info=%s' % (deps_file),
                        '++json=%s' % (ranks_build_file), '++buildable'
                    ])

            label = None
            if self.args.version == 'develop':
                label = 'develop'
                gen_lib_data(branch='develop', rebuild=True)
            elif self.args.version == 'master':
                label = 'master'
                gen_lib_data(branch='master', rebuild=True)
            elif self.args.version:
                label = 'boost-%s' % (self.args.version)
                gen_lib_data(tag='boost-%s' % (self.args.version))

            self.__save_data__(
                os.path.join(
                    self.args.out_dir, 'package-data-%s.json' % (label)),
                self.__generate_package_data__(label, data_dir))

    def __generate_package_data__(self, label, data_dir):
        if not label:
            return

        print('[GEN PACKAGE DATA %s]' % (label))
        package_data = {}

        # Read in the deps, ranks build, and ranks headers data.
        deps_file = os.path.join(data_dir, '%s-deps.json' % (label))
        deps_data = LibraryData(self.args)
        deps_data.load_dependency_info(deps_file)

        ranks_build_file = os.path.join(
            data_dir, '%s-ranks-build.json' % (label))
        ranks_build_data = LibraryData(self.args)
        ranks_build_data.load_ranks_info(ranks_build_file)

        ranks_headers_file = os.path.join(
            data_dir, '%s-ranks-headers.json' % (label))
        ranks_headers_data = LibraryData(self.args)
        ranks_headers_data.load_dependency_info(ranks_headers_file)

        # First we create the synthetic cycle group packages.
        cycle_groups = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        # We go through each build rank as that gives us the dependencies we
        # need for building.
        for rank_info in ranks_build_data.ranks_info:
            if rank_info['is_cycle']:
                name = 'cycle_group_'+cycle_groups.pop(0)
                # A cycle, being a collection of the libraries in that cycle,
                # needs to accumulate all the different aspects of each of
                # the components.
                header_only_libs = set()
                b2_requires = set()
                source_only_deps = set()
                for lib in rank_info['libs']:
                    if not deps_data.dependency_info[lib]['buildable']:
                        header_only_libs.add(lib)
                    b2_requires.update(set(
                        deps_data.dependency_info[lib]['header_deps']))
                    source_only_deps.update(set(
                        deps_data.dependency_info[lib]['source_deps']))
                    package_data[self.__clean_name__(lib)] = \
                        self.__make_lib_package_data__(
                            name=lib,
                            cycle_group=name,
                            lib_short_names=[lib],
                            b2_requires=[name],
                            header_only_libs=[] if deps_data.dependency_info[
                                lib]['buildable'] else [lib])
                source_only_deps.difference_update(b2_requires)
                b2_requires.difference_update(set(rank_info['libs']))
                package_data[name] = self.__make_lib_package_data__(
                    name=name,
                    lib_short_names=rank_info['libs'],
                    header_only_libs=header_only_libs,
                    b2_requires=b2_requires,
                    source_only_deps=source_only_deps)
        for boost_lib in deps_data.dependency_info.keys():
            if boost_lib not in package_data:
                # We add libraries that are not in a cycle at this point as
                # libraries in cycles where already filled in above.
                lib_data = deps_data.dependency_info[boost_lib]
                b2_requires = list(lib_data['header_deps'])
                # Source dependencies are only needed during the build.
                source_only_deps = []
                for source_dep in lib_data['source_deps']:
                    if deps_data.dependency_info[source_dep]['buildable']:
                        # A source dependency that itself is buildable needs
                        # to be a regular dependency so that we get the
                        # transitive build information.
                        b2_requires.append(source_dep)
                    else:
                        # For header only source dependencies we just need the
                        # headers. As we will be sideloading those during the
                        # build only.
                        source_only_deps.append(source_dep)
                # To have conistent diffs for the gnerated data we sort the
                # lists.
                package_data[self.__clean_name__(boost_lib)] = \
                    self.__make_lib_package_data__(
                        name=boost_lib,
                        lib_short_names=[boost_lib],
                        header_only_libs=[] if lib_data[
                            'buildable'] else [boost_lib],
                        b2_requires=b2_requires,
                        source_only_deps=source_only_deps
                )

        return package_data

    def __make_lib_package_data__(
        self, name,
        cycle_group=None,
        lib_short_names=[],
        header_only_libs=[],
        b2_requires=[],
        source_only_deps=[]
    ):
        return {
            'name': self.__clean_name__(name),
            'cycle_group': cycle_group,
            'lib_short_names': self.__clean_names__(lib_short_names),
            'header_only_libs': self.__clean_names__(header_only_libs),
            'b2_requires': self.__clean_names__(b2_requires),
            'source_only_deps': self.__clean_names__(source_only_deps)}

    def __clean_name__(self, name):
        return name.replace('~', '_')

    def __clean_names__(self, names):
        return [name.replace('~', '_') for name in sorted(names)]


if __name__ == "__main__":
    PackageGen()
