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
from bls.util import PushDir
from foreach import ForEach


script_dir = os.path.dirname(os.path.realpath(__file__))
recipes_dir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(script_dir))))


class CreateAll(ForEach):
    '''
    Creates, i.e. "conan create", all the Boos packages possible.
    '''

    def __init_parser__(self, parser):
        super(CreateAll, self).__init_parser__(parser)
        parser.add_argument(
            '++base-version',
            help='The version of boost_base package.',
            required=True)
        parser.add_argument(
            '++user',
            help='The user, i.e. realm, to create packages in.',
            required=True)
        parser.add_argument(
            '++channel',
            help='The channel to create packages in.',
            required=True)
        parser.add_argument(
            'create',
            help='Arguments to pass to the "conan create" invocations.',
            nargs='*',
            default=[])

    def groups_pre(self, groups):
        self.__check_call__([
            'conan', 'remove', '-f', 'boost_*'
        ])
        self.__call__([
            "conan", "remote", "add", "bincrafters",
            "https://api.bintray.com/conan/bincrafters/public-conan",
        ])
        super(CreateAll, self).groups_pre(groups)

    def package_do(self, package):
        super(CreateAll, self).package_do(package)
        print('>>>>>>>>>>')
        print('>>>>>>>>>> '+package)
        print('>>>>>>>>>>')
        sys.stdout.flush()
        package_name = 'boost_'+package
        package_version = self.args.version
        if package == 'base':
            package_version = self.args.base_version
        package_dir = os.path.join(
            recipes_dir, package_name, package_version)
        if not os.path.exists(package_dir):
            package_dir = os.path.join(
                recipes_dir, package_name, 'all')
        if os.path.isdir(package_dir):
            with PushDir(package_dir) as _:
                self.__check_call__([
                    'conan', 'create', '.', '%s/%s@%s/%s' % (
                        package_name, package_version,
                        self.args.user, self.args.channel),
                    "--build=missing"
                ]+self.args.create)


if __name__ == "__main__":
    CreateAll()
