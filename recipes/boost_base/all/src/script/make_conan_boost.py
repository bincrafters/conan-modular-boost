#!/usr/bin/env python3
"""
    Copyright (C) 2019-2020 Rene Rivera.
    Use, modification and distribution are subject to the
    Boost Software License, Version 1.0. (See accompanying file
    LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
"""
import os.path
import sys
from pprint import pprint
from bls.util import PushDir
from foreach import ForEach
import yaml
import shutil
import glob


script_dir = os.path.dirname(os.path.realpath(__file__))
recipes_dir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(script_dir))))


class MakeConanBoost(ForEach):
    '''
    Makes all the possible Conan Boost packages.
    '''

    conanfile_py = '''\
from conans import ConanFile


class Boost{proper_name}Conan(ConanFile):
    name = "{name}"
    short_paths = True
    python_requires = "boost_base/{base_ref}"
    python_requires_extend = "boost_base.BoostBaseConan"
'''

    def __init_parser__(self, parser):
        super(MakeConanBoost, self).__init_parser__(parser)
        parser.add_argument(
            '++base-ref',
            help='The version@user/channel of boost_base package.',
            required=True)

    def package_do(self, package):
        super(MakeConanBoost, self).package_do(package)
        if package != 'base':
            print("==== GENERATE: %s" % (package))
            name = "".join([n.capitalize() for n in package.split("_")])
            defs = {
                'base_ref': self.args.base_ref,
                'proper_name': name,
                'name': "boost_"+package
            }
            if self.args.trace:
                print("---- DEFS:")
                pprint(defs)
            with PushDir("boost_"+package) as package_dir:
                # Generate config.yml to add the new version.
                config_yml_path = os.path.join(package_dir, 'config.yml')
                config_yml = {}
                # We read in the existing config.yml, if any, to not loose
                # previous revision information.
                if os.path.exists(config_yml_path):
                    with open(config_yml_path, 'r', encoding='UTF-8') as f:
                        config_yml = yaml.safe_load(f)
                # Set our version information. If it exists we clobber it
                # assuming that we are regenerating.
                if 'versions' not in config_yml:
                    config_yml = {'versions': {}}
                config_yml['versions'][self.args.version] = {
                    'folder': 'all'
                }
                # Save out the updated config.yml info.
                with open(config_yml_path, 'w', encoding='UTF-8') as f:
                    yaml.safe_dump(config_yml, f)
                # Generate the updated package files.
                with PushDir('all') as package_dir:
                    # Write out the minimal conanfile.py. Again if it exists
                    # we overwrite assuming we are regenerating.
                    conanfile_py_path = os.path.join(
                        package_dir, 'conanfile.py')
                    with open(conanfile_py_path, "w", encoding='UTF-8') as f:
                        f.write(self.conanfile_py.format(**defs))
                    # Copy in the test package to the version specific package.
                    test_package_source_dir = os.path.join(
                        os.path.dirname(script_dir),
                        'test_package', package)
                    if os.path.exists(test_package_source_dir):
                        if self.args.trace:
                            print("---- Copy test_package from %s" %
                                  (test_package_source_dir))
                        with PushDir('test_package') as test_package_dir:
                            for old_file in glob.glob(
                                    os.path.join(test_package_dir, '*')):
                                if os.path.isdir(old_file):
                                    shutil.rmtree(old_file)
                                else:
                                    os.remove(old_file)
                            for test_file in glob.glob(
                                    os.path.join(test_package_source_dir, '*')):
                                shutil.copy2(test_file, os.path.join(
                                    test_package_dir, os.path.basename(test_file)))


if __name__ == "__main__":
    MakeConanBoost()
