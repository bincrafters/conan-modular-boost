#!/usr/bin/env python3
"""
    Copyright (C) 2019 Rene Rivera.
    Use, modification and distribution are subject to the
    Boost Software License, Version 1.0. (See accompanying file
    LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
"""
import os.path
import sys
from pprint import pprint
from bls.git_tool import Git
from bls.util import Main, PushDir
from bls.lib_data import LibraryData


script_dir = os.path.dirname(os.path.realpath(__file__))
recipes_dir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(script_dir))))


class ForEach(Main):
    '''
    Common base that encapsulates executing commands for all the Boost
    packages in correct dependency order.
    '''

    def __init_parser__(self, parser):
        parser.add_argument(
            '++version',
            help='The version of Boost to process.',
            required=True)
        parser.add_argument(
            '++recipes-dir',
            help='The directory of where to place the resulting recipes.'+
                ' Default is "<cci>/recipes".',
            default=recipes_dir)

    def __run__(self):
        label = None
        if self.args.version == 'develop':
            label = 'develop'
        elif self.args.version == 'master':
            label = 'master'
        elif self.args.version:
            label = 'boost-%s' % (self.args.version)
        data_dir = os.path.realpath(os.path.join(
            os.path.dirname(script_dir), '..', 'src', 'data'))
        data_file = os.path.join(data_dir, 'package-data-%s.json' % (label))

        # Generate the build DAG..

        self.package_data = self.__load_data__(data_file)

        # Build simple dependency data.
        package_deps = {}
        # Add the "bootstrap" core dependencies.
        # package_deps['build'] = set()
        # package_deps['base'] = set(['build'])
        package_deps['base'] = set()
        #
        for lib, info in self.package_data.items():
            # All packages depend on the base.
            lib_deps = set(['base'])
            # Add regular and build only deps.
            lib_deps |= set(info['b2_requires'])
            lib_deps |= set(info['source_only_deps'])
            # Record the deps.
            package_deps[lib] = lib_deps

        # Generate build groups in DAG order by decimating the deps graph.
        groups = []
        while len(package_deps) > 0:
            # Each group contains all the packages that have no deps.
            group = set()
            for package, deps in package_deps.items():
                if len(deps) == 0:
                    group.add(package)
            groups.append(group)
            print(">>>> GROUP: %s" % (group))
            if len(group) == 0:
                pprint(package_deps)
                exit(1)
            # We now remove the group members as they are accounted for.
            for package in group:
                del package_deps[package]
            # Decimate the graph to remove this group.
            for package in package_deps.keys():
                package_deps[package] -= group
        sys.stdout.flush()

        os.environ['CONAN_VERBOSE_TRACEBACK'] = '1'

        # We can now go through the groups in the DAG order.
        self.foreach(groups)

    def foreach(self, groups):
        # We can now go through the groups in the DAG order. But do it by
        # some method calls to allow customizing any part of the
        # process.
        with PushDir(self.args.recipes_dir) as _:
            self.groups_pre(groups)
            self.groups_foreach(groups)
            self.groups_post(groups)

    def groups_pre(self, groups):
        '''
        Called before processing all the groups. It calls `group_pre` for each
        group in DAG order.
        '''
        for group in groups:
            self.group_pre(group)

    def groups_foreach(self, groups):
        '''
        Called to process all the groups. It calls `group_foreach` for each
        group in DAG order.
        '''
        for group in groups:
            self.group_foreach(group)

    def groups_post(self, groups):
        '''
        Called after processing all the groups. It calls `group_post` for each
        group in DAG order.
        '''
        for group in groups:
            self.group_post(group)

    def group_pre(self, group):
        '''
        Called before processing all the packages in a group. It calls
        `package_pre` for each package in an arbitrary order.
        '''
        for package in group:
            self.package_pre(package)

    def group_foreach(self, group):
        '''
        Called to process all the packages in a group. It calls `package_do`
        for each package in an arbitrary order.
        '''
        for package in group:
            self.package_do(package)

    def group_post(self, group):
        '''
        Called after processing all the packages in a group. It calls
        `package_post` for each package in an arbitrary order.
        '''
        for package in group:
            self.package_post(package)

    def package_pre(self, package):
        '''
        Called before all packages are procesed for one `package`. Default
        does nothing.
        '''
        pass

    def package_do(self, package):
        '''
        Called while processing packages for one `package`. Default
        does nothing.
        '''
        pass

    def package_post(self, package):
        '''
        Called after all packages are procesed for one `package`. Default
        does nothing.
        '''
        pass
