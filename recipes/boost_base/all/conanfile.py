from conans import ConanFile, tools, load
from conans.util.files import save
from conans.model.conan_file import create_options
import os
import json
import glob
import locale
import subprocess
import sys


boost_conan_mixins = []


class BoostBaseConan(ConanFile):
    '''
    This is the base class to all the Boost modular packages. It combines
    what used to be multiple utility packages and generators into a single
    centralized script. It's main duties include: using the Boost library
    data for dependency information, uniform settings, uniform options,
    generate B2 scripts for building, generate B2 scripts for inter-package
    consumption, mapping Conan settings to B2 features, configuring common
    package options, and customization mixins. It is used in the individual
    Boost packages with the use of `python_requires`.
    '''

    # These are the base definitions for this base packages.
    name = "boost_base"
    description = "Shared python code used in other Conan recipes for the" + \
        "Boost libraries"
    # We export some source files that are used during building each library.
    exports = [
        # These contain general package information, like dependencies, for
        # each release version we understand.
        "src/data/package-data-boost-*.json",
        # This is a utility to compute the Windows short path from a full path.
        "src/script/short_path.cmd",
        # B2 template files for per library building.
        "src/template/*.jam"]

    # These are the definitions common to all Boost packages..

    # Public definitions of package meta-data.
    homepage = "https://boost.org/"
    url = "https://github.com/conan-io/conan-center-index"
    license = "MIT"

    # Private definitions for operation of recipe.

    # GitHub location for Boost organization to fetch module archives from.
    website = "https://github.com/boostorg"

    # Building Boost generates long paths. This helps in avoiding problems on
    # platforms where long paths are a problem.
    short_paths = True

    settings = "os", "arch", "compiler", "build_type"

    # Maps from the base package name to the subrepo in BoostOrg GitHub source.
    boost_source_repo = {
        'numeric_interval': "interval",
        'numeric_odeint': "odeint",
        'numeric_ublas': "ublas"
    }

    # Data, like conandata.yml, for configuring based on the Boost version.
    # This would normally be in conandata.yml, but that doesn't allow arbitrary
    # keys.
    boost_data = {
        'boost_info': {
            '1.71.0': {
                'b2_version': '4.0.1'
            }
        }
    }

    #
    # Redefinitions for ConanFile package properties. These are dynamically
    # computed from the Boost libraries meta-data.
    #

    @property
    def no_copy_source(self):
        return self.is_base

    #
    # Information on this base class, irrespective of the instance class.
    #

    @property
    def is_base(self):
        return self.__class__.__name__ == "BoostBaseConan"

    @property
    def base_source_path(self):
        '''
        This is the path to the sources for this base package. When we are
        building a subclassed package we need this to get access to the
        exported data and template files.
        '''
        if not hasattr(self, '_base_source_path_'):
            self._base_source_path_ = os.path.dirname(
                os.path.abspath(__file__))
        return self._base_source_path_

    def boost_init(self):
        '''
        Prepares the instance with all information needed for the various Conan
        steps. Mostly provides default, empty, values for the Boost custom
        information. For member values the subclass can provide a "get_<name>"
        method to dynamically compute the value.
        '''
        if self.is_base:
            return
        if self.__class__.__name__ == "TestPackageConan":
            self._boost_data_ = {
                "test_package_conan": {
                    "b2_requires": [],
                    "cycle_group": None,
                    "header_only_libs": ["test_package_conan"],
                    "lib_short_names": ["test_package_conan"],
                    "name": "test_package_conan",
                    "source_only_deps": []
                }
            }
        if not hasattr(self, '_boost_data_'):
            json_file = os.path.join(
                self.base_source_path,
                'src', 'data',
                'package-data-boost-{0}.json'.format(self.version))
            with open(json_file, "r") as f:
                self._boost_data_ = json.load(f)

    #
    # Properties for the Boost package instance. These generally correspond
    # to the Conan properties but for the Boost specific data.
    #

    @property
    def boost_name(self):
        '''
        Basename of the Boost library this package contains. I.e. the name
        of the package without the "boost_" prefix.
        '''
        if not hasattr(self, '_boost_name_'):
            self._boost_name_ = self.name.replace('boost_', '')
        return self._boost_name_

    @property
    def boost_requires(self):
        '''
        What other Boost libraries we require as dependencies. Empty list if
        none.
        '''
        self.boost_init()
        return self._boost_data_[self.boost_name]['b2_requires']

    @property
    def boost_build_requires(self):
        '''
        What other Boost libraries we require as dependencies for building
        only. Empty list if none.
        '''
        return []

    @property
    def boost_build_defines(self):
        '''
        Preprocessor definitions to use during building only.
        '''
        result = set()
        for mixin in self.boost_mixins:
            result.union(set(mixin.boost_build_defines))
        return list(sorted(result))

    @property
    def boost_build_options(self):
        '''
        Dictionary of B2 "key=value" arguments to use when building
        the package library(ies).
        '''
        result = {}
        for mixin in self.boost_mixins:
            result.update(mixin.boost_build_options)
        return result

    @property
    def boost_cycle_group(self):
        '''
        The name of the cycle group, if this is a cycle group. Otherwise
        "None".
        '''
        self.boost_init()
        return self._boost_data_[self.boost_name]['cycle_group']

    @property
    def boost_libs(self):
        '''
        The libraries making up this package. For cycle groups this is two or
        more, otherwise just the one.
        '''
        self.boost_init()
        return self._boost_data_[self.boost_name]['lib_short_names']

    @property
    def boost_header_only_libs(self):
        '''
        The subset of libraries in the package that do not need to be built.
        '''
        self.boost_init()
        return self._boost_data_[self.boost_name]['header_only_libs']

    @property
    def boost_libs_to_build(self):
        '''
        The libraries that need building with B2. I.e. non-header only libs.
        '''
        if not hasattr(self, '_boost_libs_to_build_'):
            self._boost_libs_to_build_ = list(
                set(self.boost_libs)-set(self.boost_header_only_libs))
        return self._boost_libs_to_build_

    @property
    def boost_source_only_deps(self):
        '''
        Libraries that we need their source only for building.
        '''
        self.boost_init()
        return self._boost_data_[self.boost_name]['source_only_deps']

    @property
    def is_cycle_group(self):
        '''
        Returns true if the package is a container for a group of packages
        that have a circular dependency.
        '''
        return "cycle_group" in self.name

    def get_b2_options(self):
        '''
        The default for b2_options is an empty dictionary, i.e. no key=value's.
        '''
        return {}

    def is_header_only(self, lib_name):
        '''
        Return true if the given lib_name library is header only and doesn't
        need building.
        '''
        return (lib_name in self.boost_header_only_libs)

    #
    # ConanFile packaging methods..
    #

    def initialize(self, settings, env):
        '''
        Initializes information about the libraries we are building, except
        when we are packaging this base class.
        '''
        if self.is_base:
            super(BoostBaseConan, self).initialize(settings, env)
        else:
            # Save our initial unmodified properties.
            base_options = BoostConanMixin(self, base_options=self)
            # The base can now muck with them.
            super(BoostBaseConan, self).initialize(settings, env)
            self.initialize_bare()
            # We copy the options from the mixins and use that to reset our
            # options.
            for mixin in self.boost_mixins:
                base_options.options.update(mixin.options)
                base_options.default_options.update(
                    mixin.default_options)
            self.options = create_options(base_options)

    def initialize_bare(self):
        if not self.is_base:
            # Load up the Boost data for the mixins to interrogate.
            self.boost_init()
            # We create all the mixins we know about and register the ones
            # that are pretinent, i.e. match, our package.
            self.boost_mixins = []
            for mixin_class in boost_conan_mixins:
                mixin = mixin_class(self)
                if mixin.matches:
                    self.boost_mixins.append(mixin)

    def configure(self):
        '''
        Automatic configuration. Takes care to apply options specified in a
        cycle group member to that cycle group.
        '''
        if self.is_base:
            return
        if self.boost_cycle_group:
            class_options = getattr(self.__class__, 'options')
            if class_options:
                for option in getattr(self.__class__, 'options').keys():
                    value = getattr(self.options, option)
                    setattr(
                        self.options[self.boost_cycle_group], option, value)

    def config_options(self):
        '''
        Gives the mixins a chance to edit package build options.
        '''
        if self.is_base:
            pass
        else:
            for mixin in self.boost_mixins:
                mixin.config_options()

    def requirements(self):
        '''
        Calculates dependency requirements to other Boost packages.
        '''
        if self.is_base:
            pass
        else:
            self.boost_init()
            # Expand out references to Boost inter-package (library)
            # dependencies.
            for lib in self.boost_requires:
                self.requires("{dep}/{ver}@{user}/{channel}".format(
                    dep='boost_'+lib,
                    ver=self.version,
                    user=self.user,
                    channel=self.channel,
                ))
            # We need B2 if we are building any libraries in the package.
            # NOTE: We use the true CCI version of B2.
            if len(self.boost_libs_to_build) > 0:
                b2_version = self.boost_data['boost_info'][self.version]['b2_version']
                self.requires("{dep}/{ver}@{user}/{channel}".format(
                    dep='b2',
                    ver=b2_version,
                    user='_',
                    channel='_',
                ))
            for mixin in self.boost_mixins:
                mixin.requirements()

    def build_requirements(self):
        '''
        Applies build only requirements from `b2_build_requires` to the
        package.
        '''
        if self.is_base:
            pass
        else:
            self.boost_init()
            # Expand out references to Boost inter-package (library)
            # dependencies.
            boost_build_requires = set(self.boost_build_requires)
            for mixin in self.boost_mixins:
                boost_build_requires.update(set(mixin.boost_build_requires))
            for lib in boost_build_requires:
                self.build_requires("{dep}/{ver}@{user}/{channel}".format(
                    dep='boost_'+lib,
                    ver=self.version,
                    user=self.user,
                    channel=self.channel,
                ))
            for mixin in self.boost_mixins:
                mixin.build_requirements()

    def source(self):
        '''
        Depending on the kind of package it is, downloads the Boost library
        sources. For a library in a cycle group we do nothing. Otherwise
        it downloads the individual libraries.
        '''
        if self.is_base:
            return
        self.boost_init()
        if not self.boost_cycle_group:
            # It's a regular library, i.e. not a cycle group alias, set up the
            # sources, including generated ones.
            archive_name = "boost-" + self.version
            # Download the source directly from GitHub library source.
            libs_to_get = self.boost_libs + self.boost_source_only_deps
            for lib in libs_to_get:
                lib_repo = lib
                if lib in self.boost_source_repo:
                    lib_repo = self.boost_source_repo[lib]
                tools.get(
                    "{0}/{1}/archive/{2}.tar.gz".format(
                        self.website, lib_repo, archive_name))
                os.rename(lib_repo + "-" + archive_name, lib)
            # If we are going to build something we need to get the matching
            # boostcpp.jam build file from the Boost super-project.
            if len(self.boost_libs_to_build) > 0:
                bootcpp_raw_url = \
                    "https://raw.githubusercontent.com/" + \
                    "boostorg/boost/boost-{0}/boostcpp.jam"
                tools.download(
                    bootcpp_raw_url.format(self.version),
                    "boostcpp.jam")

        for mixin in self.boost_mixins:
            mixin.source()

    def build(self):
        '''
        Build any buildable, i.e. not header only, libraries in the package.
        Building is done for any package that is not in a cycle group. As cycle
        group members just steal the produced builds from the cycle group.
        The main build procedure iterates for each library building them as
        needed and creating the export structure and files.
        '''
        if self.is_base:
            return

        self.boost_init()

        # Libraries that are in a cycle group are not built directly. Instead
        # the results are taken from the cycle group. Hence there's nothing
        # to do here.
        if self.boost_cycle_group:
            return

        if len(self.boost_libs_to_build) > 0:
            # Create local jamroot for build that defines magic rules,
            # hooks, variables and targets to control the build for Conan.
            self._write_jamroot_jam()
            # Create local project-config.jam for setting up B2.
            self._write_project_config_jam()
            # Also write out the utility Windows short path script.
            self._write_short_path_cmd()

        # Build each library.
        for lib in self.boost_libs:
            self._build_lib(lib)
            for mixin in self.boost_mixins:
                mixin.build_lib(lib)

    def _write_jamroot_jam(self):
        '''
        Generates the `jamroot.jam` file at the root of the package build tree.
        This jamfile contains most of the configuration, and patching magic,
        to build the individual libraries.
        '''
        # TODO: Rewrite to use a less kludgy template system.
        content = load(os.path.join(
            self.base_source_path, 'src', 'template', 'jamroot.jam'))
        jam_include_paths = ' '.join(
            '"' + path + '"' for path in self.deps_cpp_info.includedirs
        ).replace('\\', '/')
        content = content \
            .replace("{{{toolset}}}", self.b2_toolset) \
            .replace("{{{libraries}}}", " ".join(self.boost_libs)) \
            .replace("{{{boost_version}}}", self.version) \
            .replace("{{{deps.include_paths}}}", jam_include_paths) \
            .replace("{{{os}}}", self.b2_os) \
            .replace("{{{address_model}}}", self.b2_address_model) \
            .replace("{{{architecture}}}", self.b2_architecture) \
            .replace(
                "{{{deps_info}}}", self._b2_dependencies_for_jamroot_jam) \
            .replace("{{{variant}}}", self.b2_variant) \
            .replace("{{{name}}}", self.name) \
            .replace("{{{link}}}", self.b2_link) \
            .replace("{{{runtime_link}}}", self.b2_runtime_link) \
            .replace("{{{toolset_version}}}", self.b2_toolset_version) \
            .replace("{{{toolset_exec}}}", self.b2_toolset_exec) \
            .replace("{{{libcxx}}}", self.b2_libcxx) \
            .replace("{{{cxxstd}}}", self.b2_cxxstd) \
            .replace("{{{cxxabi}}}", self.b2_cxxabi) \
            .replace("{{{libpath}}}", self.b2_icu_lib_paths) \
            .replace("{{{arch_flags}}}", self.b2_arch_flags) \
            .replace("{{{isysroot}}}", self.b2_isysroot) \
            .replace("{{{os_version}}}", self.b2_os_version) \
            .replace("{{{fpic}}}", self.b2_fpic) \
            .replace("{{{threading}}}", self.b2_threading) \
            .replace("{{{threadapi}}}", self.b2_threadapi) \
            .replace("{{{profile_flags}}}", self.b2_profile_flags)
        save(os.path.join(self.build_folder, 'jamroot.jam'), content)

    def _write_project_config_jam(self):
        '''
        Generates the `project-config.jam` file at the root of the build tree.
        This file contains the configuration that maps from the Conan provided
        tool and packaged libraries to the B2 equivalent.
        '''
        # TODO: Rewrite to use a less kludgy template system.
        content = load(os.path.join(
            self.base_source_path, 'src', 'template', 'project-config.jam'))
        content = content \
            .replace("{{{toolset}}}", self.b2_toolset) \
            .replace("{{{toolset_version}}}", self.b2_toolset_version) \
            .replace("{{{toolset_exec}}}", self.b2_toolset_exec) \
            .replace("{{{zlib_lib_paths}}}", self.zlib_lib_paths) \
            .replace("{{{zlib_include_paths}}}", self.zlib_include_paths) \
            .replace("{{{zlib_name}}}", self.zlib_lib_name) \
            .replace("{{{bzip2_lib_paths}}}", self.bzip2_lib_paths) \
            .replace("{{{bzip2_include_paths}}}", self.bzip2_include_paths) \
            .replace("{{{bzip2_name}}}", self.bzip2_lib_name) \
            .replace("{{{lzma_lib_paths}}}", self.lzma_lib_paths) \
            .replace("{{{lzma_include_paths}}}", self.lzma_include_paths) \
            .replace("{{{lzma_name}}}", self.lzma_lib_name) \
            .replace("{{{zstd_lib_paths}}}", self.zstd_lib_paths) \
            .replace("{{{zstd_include_paths}}}", self.zstd_include_paths) \
            .replace("{{{zstd_name}}}", self.zstd_lib_name) \
            .replace("{{{python_exec}}}", self.b2_python_exec) \
            .replace("{{{python_version}}}", self.b2_python_version) \
            .replace("{{{python_include}}}", self.b2_python_include) \
            .replace("{{{python_lib}}}", self.b2_python_lib) \
            .replace("{{{mpicxx}}}", self.b2_mpicxx) \
            .replace("{{{profile_tools}}}", self.b2_profile_tools)
        save(os.path.join(self.build_folder, 'project-config.jam'), content)

    def _write_short_path_cmd(self):
        '''
        Copy the `short_path.cmd` script to where the B2 build script, the
        `jamroot.jam` file, expects it during the build, i.e. to the root
        of the build tree.
        '''
        content = load(os.path.join(
            self.base_source_path, 'src', 'script', 'short_path.cmd'))
        save(os.path.join(self.build_folder, 'short_path.cmd'), content)

    @property
    def _b2_dependencies_for_jamroot_jam(self):
        '''
        Computes dependency declarations for the package jamroot.
        '''
        deps_info = []
        for dep_name, dep_cpp_info in self.deps_cpp_info.dependencies:
            for libdir in dep_cpp_info.libdirs:
                dep_libdir = os.path.join(dep_cpp_info.rootpath, libdir)
                if os.path.isfile(os.path.join(dep_libdir, "jamroot.jam")):
                    lib_short_name = \
                        os.path.basename(os.path.dirname(dep_libdir))
                    lib_project_name = \
                        "\"/" + dep_name + "," + lib_short_name + "\""
                    deps_info.append('use-project %s : "%s" ;' % (
                        lib_project_name, dep_libdir.replace('\\', '/')))
                    deps_info.append('alias "%s" : %s ;' % (
                        lib_short_name, lib_project_name))
                    dep_libs = \
                        self._boost_data_[lib_short_name]['lib_short_names']
                    for dep_lib in dep_libs:
                        deps_info.append('"LIBRARY_DIR(%s)" = "%s" ;' % (
                            dep_lib, dep_libdir.replace('\\', '/')))

        deps_info = "\n".join(deps_info)
        return deps_info

    def _build_lib(self, lib):
        # We put all files needed to use the library in the lib dir.
        lib_dir = os.path.join(lib, "lib")
        # Each lib gets a jamroot.jam that is used to import it when
        # building downstream packages. This jamroot.jam is nly used
        # for further building and not for consumers of the packages.
        jam_file = os.path.join(lib_dir, "jamroot.jam")
        if self.is_header_only(lib):
            # Header only libs only get the jamroot.jam file in the lib
            # exported dir.
            jamroot_content = self.jamroot_header_only_content.format(
                lib=lib)
            tools.save(jam_file, jamroot_content, append=True)
        else:
            # Construct the B2 build command:
            b2_command = [
                # B2 executable, which comes in as a dependency.
                "b2",
                # Use all available for parallel build.
                "-j%s" % (tools.cpu_count()),
                # Optionally add debug output information. Default of +d1
                # just shows the actions executed.
                "-d+%s" % (os.getenv('CONAN_B2_DEBUG', '1')),
                # We need to do full rebuilds.
                "-a",
                # Avoid long intermediate paths by using hashed variant
                # dirs.
                "--hash=yes",
                # We always print out configuration info to aid in build
                # debugging.
                "--debug-configuration",
                # We use the bare "system" naming that avoids extra
                # tagging. This simplifies the logic for finding and using
                # specific libraries. And we don't need the extended
                # tagging as Conan segregates variants similarly like B2.
                "--layout=system"
            ]
            # Add the B2 features needed as defined by the package.
            b2_command += [
                key + "=" + value
                for key, value in self.boost_build_options.items()]
            # Add cpp defines as needed.
            b2_command += [
                "define=" + define
                for define in self.boost_build_defines]
            # Add include dirs of source only dependencies nneded for
            # building.
            b2_command += [
                "include=" + lib + '/include'
                for lib in self.boost_source_only_deps]
            # Finally, add the target we build. This is a special target
            # that build just the library we need.
            b2_command += [lib + "-build"]
            # Lets now do the build, but first debug output what we are
            # about to run.
            self.output.info(
                "%s: %s" % (os.getcwd(), " ".join(b2_command)))
            # TODO: Why do we add ${MPI_BIN} to PATH?
            with tools.environment_append({
                'PATH': [os.getenv('MPI_BIN', '')]
            }):
                self.run(" ".join(b2_command))

            # For each library built add to the exported jamroot.jam
            # information about that library.
            libs = self._collect_build_libs(lib_dir)
            for lib_link_name in libs:
                search_content = self.jamroot_search_content.format(
                    lib_link_name=lib_link_name)
                tools.save(jam_file, search_content, append=True)

            # If we didn't build a "canonical" boost_<name> library we add
            # an alias target to point to all the built libraries to the
            # exported jamroot.jam.
            if "boost_" + lib not in libs:
                alias_content = self.jamroot_alias_content.format(
                    lib=lib,
                    space_joined_libs=" ".join(libs))
                tools.save(jam_file, alias_content, append=True)

    # Jamroot.jam for header only libs. It declares:
    # ROOT({lib}) -- path to the root of the exported package.
    # /conan/{lib} -- project requirements.
    # /boost/{lib} -- global ID to mirror Boost project IDs.
    jamroot_header_only_content = """\
import project ;
import path ;
import modules ;
ROOT({lib}) = [ path.parent [ path.parent [ path.make
    [ modules.binding $(__name__) ] ] ] ] ;
project /conan/{lib} : requirements <include>$(ROOT({lib}))/include ;
project.register-id /boost/{lib} : $(__name__) ;
"""

    # Jamroot.jam content for built libraries that adds the lib target(s) that
    # other Boost packages will use to link in their dependencies.
    jamroot_search_content = """\
lib {lib_link_name} : : <name>{lib_link_name} <search>. : : $(usage) ;
"""

    # Jamroot.jam content for built libraries that aliases the one or more
    # built libraries as a single symbolic target for use as a single name
    # build dependency.
    jamroot_alias_content = """\
alias boost_{lib} : {space_joined_libs} : : : $(usage) ;
"""

    def _collect_build_libs(self, lib_folder):
        '''
        Searches the build output for any libraries built and returns the
        simple basename of those libraries.
        '''
        libs = []
        if not os.path.exists(lib_folder):
            self.output.warn(
                "Lib folder doesn't exist, can't collect libraries: " +
                lib_folder)
        else:
            files = os.listdir(lib_folder)
            for f in files:
                name, ext = os.path.splitext(f)
                if ext in (".so", ".lib", ".a", ".dylib"):
                    if ext != ".lib" and name.startswith("lib"):
                        name = name[3:]
                    libs.append(name)
        return libs

    def package(self):
        '''
        Package the exported files from all the libraries we built.
        '''
        if self.is_base:
            self.copy("LICENSE.txt", dst="licenses", src="src")
        else:
            self.boost_init()
            for lib in self.boost_libs:
                self.copy(pattern="*LICENSE*", dst="licenses", src=lib)
                for subdir in ["lib", "include"]:
                    copydir = os.path.join(lib, subdir)
                    self.copy(pattern="*", dst=copydir, src=copydir)
            for mixin in self.boost_mixins:
                mixin.package()

    def package_info(self):
        '''
        Generate the meta information about the libraries in the package.
        '''
        if self.is_base:
            return
        self.boost_init()

        # We publish a single comma separated list of the libraries in the
        # package user info.
        self.user_info.boost_libs = ",".join(self.boost_libs)

        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.libs = []

        if self.is_cycle_group:
            # For a group of circular dependent libs we publish the aggregation
            # of the lib and include dirs.
            for lib in self.boost_libs:
                lib_dir = os.path.join(lib, "lib")
                self.cpp_info.libdirs.append(lib_dir)
                include_dir = os.path.join(lib, "include")
                self.cpp_info.includedirs.append(include_dir)
        elif self.boost_cycle_group:
            # For a library in a cycle group we steal some info from the cycle
            # group. Hence this ends up "aliasing" the group content.
            group = self.deps_cpp_info['boost_'+self.boost_cycle_group]
            # Point the include dir to the group sublib include dir.
            include_dir = os.path.join(
                group.rootpath, self.boost_libs[0], "include")
            self.cpp_info.includedirs.append(include_dir)
            # Point the lib dir to the group sublib lib dir.
            lib_dir = os.path.join(
                group.rootpath, self.boost_libs[0], "lib")
            self.cpp_info.libdirs.append(lib_dir)
            # And if this lib had built files, we add all the found libs from
            # the group sublib lib dir to this package. This has the effect
            # of consumer linking to the sublib specific targets only.
            if not self.is_header_only(self.boost_libs[0]):
                self.cpp_info.libs.extend(tools.collect_libs(self, lib_dir))
        else:
            # Otherwise we are a regular built lib and can add include dir,
            # lib dir, and libs directly in this package.
            include_dir = os.path.join(self.boost_libs[0], "include")
            self.cpp_info.includedirs.append(include_dir)
            lib_dir = os.path.join(self.boost_libs[0], "lib")
            self.cpp_info.libdirs.append(lib_dir)
            if not self.is_header_only(self.boost_libs[0]):
                self.cpp_info.libs.extend(tools.collect_libs(self, lib_dir))

        # Since we explicitly specify all the libs we need to use we turn off
        # the Boost built-in mechanism for automatic linking of libraries on
        # some platforms (i.e. MSVC)
        self.cpp_info.defines.append("BOOST_ALL_NO_LIB=1")
        self.cpp_info.bindirs.extend(self.cpp_info.libdirs)
        # Avoid duplicate entries in the libs.
        self.cpp_info.libs = list(set(self.cpp_info.libs))

        for mixin in self.boost_mixins:
            mixin.package_info()

    def package_id(self):
        '''
        We need to account for the package ID being different if it's just the
        base or library package.
        '''
        if self.is_base:
            # This base is simply a shell, that doesn't build anything for
            # itself.
            self.info.header_only()
        else:
            self.boost_init()
            # We can only be header only when all the sub parts are header
            # only.
            all_header_only = True
            for lib in self.boost_libs:
                all_header_only = all_header_only and self.is_header_only(lib)
            if all_header_only:
                self.info.header_only()
            # For all the package requirements that are Boost packages we
            # indicate that the version matching can't use partial versions
            # as acceptable. This avoids having one Boost library package
            # accidentally depend on a different version. I.e. that all the
            # Boost libraries advance versions in lockstep.
            # Revisit if Boost ever supports cross-version dependencies.
            boost_deps_only = [
                dep_name
                for dep_name in self.info.requires.pkg_names
                if dep_name.startswith("boost_")]
            for dep_name in boost_deps_only:
                self.info.requires[dep_name].full_version_mode()

            for mixin in self.boost_mixins:
                mixin.package_id()

    #
    # Translation of Conan to B2 equivalents..
    #

    _b2_os = {
        'Windows': 'windows',
        'Linux': 'linux',
        'Macos': 'darwin',
        'Android': 'android',
        'iOS': 'iphone',
        'FreeBSD': 'freebsd',
        'SunOS': 'solaris'}

    @property
    def b2_os(self):
        return self._b2_os[str(self.settings.os)]

    _b2_address_model = {
        'x86': '32',
        'x86_64': '64',
        'ppc64le': '64',
        'ppc64': '64',
        'armv6': '32',
        'armv7': '32',
        'armv7hf': '32',
        'armv8': '64'}

    @property
    def b2_address_model(self):
        return self._b2_address_model[str(self.settings.arch)]

    @property
    def b2_architecture(self):
        if str(self.settings.arch).startswith('x86'):
            return 'x86'
        elif str(self.settings.arch).startswith('ppc'):
            return 'power'
        elif str(self.settings.arch).startswith('arm'):
            return 'arm'
        else:
            return ""

    @property
    def b2_variant(self):
        if str(self.settings.build_type) == "Debug":
            return "debug"
        else:
            return "release"

    _b2_toolsets = {
        'gcc': 'gcc',
        'Visual Studio': 'msvc',
        'clang': 'clang',
        'apple-clang': 'clang'}

    @property
    def b2_toolset(self):
        return self._b2_toolsets[str(self.settings.compiler)]

    _b2_msvc_version = {
        '8': '8.0',
        '9': '9.0',
        '10': '10.0',
        '11': '11.0',
        '12': '12.0',
        '15': '14.1',
        '16': '14.2'
    }

    @property
    def b2_toolset_version(self):
        if self.settings.compiler == "Visual Studio":
            return self._b2_msvc_version[str(self.settings.compiler.version)]
        else:
            return "$(DEFAULT)"

    @property
    def b2_toolset_exec(self):
        class dev_null(object):
            def write(self, message):
                pass
        if bool(
            (self.b2_os in [
                'linux', 'freebsd', 'solaris', 'darwin', 'android']) or
            (self.b2_os == 'windows' and self.b2_toolset == 'gcc')
        ):
            if 'CXX' in os.environ:
                try:
                    self.run(
                        os.environ['CXX'] + ' --version',
                        output=dev_null())
                    return os.environ['CXX']
                except:
                    pass
            version = str(self.settings.compiler.version).split('.')
            result_x = self.b2_toolset.replace('gcc', 'g++') + "-" + version[0]
            result_xy = result_x
            if len(version) > 1:
                result_xy += version[1] if version[1] != '0' else ''
            try:
                self.run(result_xy + " --version", output=dev_null())
                return result_xy
            except:
                pass
            try:
                self.run(result_x + " --version", output=dev_null())
                return result_x
            except:
                pass
            return "$(DEFAULT)"
        elif self.b2_os == "windows":
            return self.b2_win_cl_exe or "$(DEFAULT)"
        else:
            return "$(DEFAULT)"

    @property
    def b2_win_cl_exe(self):
        vs_root = tools.vs_installation_path(
            str(self.settings.compiler.version))
        if vs_root:
            cl_exe = \
                glob.glob(os.path.join(
                    vs_root, "VC", "Tools", "MSVC", "*", "bin", "*", "*",
                    "cl.exe")) + \
                glob.glob(os.path.join(vs_root, "VC", "bin", "cl.exe"))
            if cl_exe:
                return cl_exe[0].replace("\\", "/")

    @property
    def b2_link(self):
        try:
            return "shared" if self.options.shared else "static"
        except:
            return "static"

    @property
    def b2_runtime_link(self):
        if bool(
                self.settings.compiler == "Visual Studio" and
                self.settings.compiler.runtime
        ):
            return "static" if "MT" in str(self.settings.compiler.runtime) \
                else "$(DEFAULT)"
        return "$(DEFAULT)"

    @property
    def b2_cxxstd(self):
        # for now, we use C++11 as default, unless we're targeting libstdc++
        # (not 11)
        if self.b2_toolset in ['gcc', 'clang'] and self.b2_os != 'android':
            if str(self.settings.compiler.libcxx) != 'libstdc++':
                return '<cxxflags>-std=c++11 <linkflags>-std=c++11'
        return ''

    @property
    def b2_cxxabi(self):
        if self.b2_toolset in ['gcc', 'clang'] and self.b2_os != 'android':
            if str(self.settings.compiler.libcxx) == 'libstdc++11':
                return '<define>_GLIBCXX_USE_CXX11_ABI=1'
            elif str(self.settings.compiler.libcxx) == 'libstdc++':
                return '<define>_GLIBCXX_USE_CXX11_ABI=0'
        return ''

    @property
    def b2_libcxx(self):
        if self.b2_toolset == 'clang' and self.b2_os != 'android':
            if str(self.settings.compiler.libcxx) == 'libc++':
                return '<cxxflags>-stdlib=libc++ <linkflags>-stdlib=libc++'
            elif str(self.settings.compiler.libcxx) in [
                'libstdc++11', 'libstdc++'
            ]:
                return \
                    '<cxxflags>-stdlib=libstdc++ <linkflags>-stdlib=libstdc++'
        return ''

    _python_dep = "python_dev_config"

    @property
    def b2_python_exec(self):
        try:
            return self.deps_user_info[
                self._python_dep].python_exec.replace('\\', '/')
        except:
            return ""

    @property
    def b2_python_version(self):
        try:
            return self.deps_user_info[
                self._python_dep].python_version.replace('\\', '/')
        except:
            return ""

    @property
    def b2_python_include(self):
        try:
            return self.deps_user_info[
                self._python_dep].python_include_dir.replace('\\', '/')
        except:
            return ""

    @property
    def b2_python_lib(self):
        try:
            if self.settings.compiler == "Visual Studio":
                return self.deps_user_info[
                    self._python_dep].python_lib_dir.replace('\\', '/')
            else:
                return self.deps_user_info[
                    self._python_dep].python_lib.replace('\\', '/')
        except:
            return ""

    @property
    def b2_icu_lib_paths(self):
        try:
            if self.options.use_icu:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["icu"].lib_paths)).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def b2_apple_arch(self):
        return {
            "armv7": "armv7",
            "armv8": "arm64",
            "x86": "i386",
            "x86_64": "x86_64"
        }.get(str(self.settings.arch))

    @property
    def b2_apple_sdk(self):
        if self.settings.os == "Macos":
            return "macosx"
        elif self.settings.os == "iOS":
            if str(self.settings.arch).startswith('x86'):
                return "iphonesimulator"
            elif str(self.settings.arch).startswith('arm'):
                return "iphoneos"
            else:
                return None
        return None

    @property
    def b2_apple_isysroot(self):
        return self.command_output([
            'xcrun', '--show-sdk-path', '-sdk', self.b2_apple_sdk])

    @property
    def b2_arch_flags(self):
        if self.b2_os == 'darwin' or self.b2_os == 'iphone':
            return '<flags>"-arch {0}" <linkflags>"-arch {0}"'.format(
                self.b2_apple_arch)
        return ''

    @property
    def b2_isysroot(self):
        if self.b2_os == 'darwin' or self.b2_os == 'iphone':
            return '<flags>"-isysroot {0}"'.format(self.b2_apple_isysroot)
        return ''

    @property
    def b2_os_version(self):
        if (self.b2_os == 'darwin' or self.b2_os == 'iphone') \
                and self.settings.get_safe("os.version"):
            return '<flags>"{0}"'.format(tools.apple_deployment_target_flag(
                self.settings.os, self.settings.os.version))
        return ''

    @property
    def b2_fpic(self):
        if self.b2_os != 'windows' and self.b2_toolset in ['gcc', 'clang'] \
                and self.b2_link == 'static':
            return '<flags>-fPIC\n<cxxflags>-fPIC'
        return ''

    @property
    def b2_mpicxx(self):
        try:
            return str(self.options.mpicxx)
        except:
            return ''

    @property
    def b2_threading(self):
        return 'multi'

    @property
    def b2_threadapi(self):
        try:
            result = str(self.options.threadapi)
            if result != 'default':
                return result
        except:
            pass
        try:
            if str(self.settings.threads) == 'posix':
                return 'pthread'
            if str(self.settings.threads) == 'win32':
                return 'win32'
        except:
            pass
        if self.b2_os == 'windows':
            return 'win32'
        else:
            return 'pthread'

    @property
    def b2_profile_flags(self):
        def format_b2_flags(token, flags):
            return '%s"%s"' % (token, flags)

        if self.b2_toolset == 'gcc' or self.b2_toolset == 'clang':
            additional_flags = []
            if 'CFLAGS' in os.environ:
                additional_flags.append(format_b2_flags(
                    '<cflags>', os.environ['CFLAGS']))
            if 'CXXFLAGS' in os.environ:
                additional_flags.append(format_b2_flags(
                    '<cxxflags>', os.environ['CXXFLAGS']))
            if 'LDFLAGS' in os.environ:
                additional_flags.append(format_b2_flags(
                    '<linkflags>', os.environ['LDFLAGS']))
            return '\n'.join(additional_flags)
        else:
            return ''

    @property
    def b2_profile_tools(self):
        if self.b2_toolset == 'gcc' or self.b2_toolset == 'clang':
            additional_flags = []
            if 'SYSROOT' in os.environ:
                additional_flags.append('<root>"%s"' % os.environ['SYSROOT'])
            if 'AR' in os.environ:
                additional_flags.append('<archiver>"%s"' % os.environ['AR'])
            if 'RANLIB' in os.environ:
                additional_flags.append('<ranlib>"%s"' % os.environ['RANLIB'])
            if self.b2_os == 'darwin' or self.b2_os == 'iphone':
                if 'STRIP' in os.environ:
                    additional_flags.append(
                        '<striper>"%s"' % os.environ['STRIP'])
            additional_flags = ' '.join(additional_flags)
            if len(additional_flags):
                additional_flags = ': ' + additional_flags
            return additional_flags
        else:
            return ''

    #
    # External library configuration information. Which is fed into B2 for the
    # setup to build.
    #

    @property
    def zlib_lib_paths(self):
        try:
            if self.options.use_zlib:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["zlib"].lib_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def zlib_include_paths(self):
        try:
            if self.options.use_zlib:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["zlib"].include_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def zlib_lib_name(self):
        try:
            if self.options.use_zlib:
                return os.path.basename(self.deps_cpp_info["zlib"].libs[0])
        except:
            pass
        return ""

    @property
    def bzip2_lib_paths(self):
        try:
            if self.options.use_bzip2:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["bzip2"].lib_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def bzip2_include_paths(self):
        try:
            if self.options.use_bzip2:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["bzip2"].include_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def bzip2_lib_name(self):
        try:
            if self.options.use_bzip2:
                return os.path.basename(self.deps_cpp_info["bzip2"].libs[0])
        except:
            pass
        return ""

    @property
    def lzma_lib_paths(self):
        try:
            if self.options.use_lzma:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["lzma"].lib_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def lzma_include_paths(self):
        try:
            if self.options.use_lzma:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["lzma"].include_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def lzma_lib_name(self):
        try:
            if self.options.use_lzma:
                return os.path.basename(self.deps_cpp_info["lzma"].libs[0])
        except:
            pass
        return ""

    @property
    def zstd_lib_paths(self):
        try:
            if self.options.use_zstd:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["zstd"].lib_paths)
                ).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def zstd_include_paths(self):
        try:
            if self.options.use_zstd:
                return '"{0}"'.format('" "'.join(
                    self.deps_cpp_info["zstd"].include_paths
                )).replace('\\', '/')
        except:
            pass
        return ""

    @property
    def zstd_lib_name(self):
        try:
            if self.options.use_zstd:
                return os.path.basename(self.deps_cpp_info["zstd"].libs[0])
        except:
            pass
        return ""

    #
    # Utilities..
    #

    def command_output(self, command):
        if sys.version_info.major >= 3:
            return subprocess.check_output(
                command, shell=False,
                encoding=locale.getpreferredencoding()).strip()
        else:
            return subprocess.check_output(command, shell=False).strip()


class BoostConanMixin(object):
    '''
    This base mixin class provides for dynamic hooks into the packaging steps.
    When a mixing is included. i.e. it matches, the current packaging context
    the `BoostBaseConan` class will invoke the callbacks herein. Consult the
    method and properties in the `BoostBaseConan` class for the effects. The
    current package being built is available as the `self.conanfile`.
    '''

    # Definitions to add to the current package.
    options = {}
    default_options = {}

    def __init__(self, conan_file, base_options=None):
        self.conanfile = conan_file
        if base_options:
            self.options = getattr(base_options, 'options')
            if not self.options:
                self.options = {}
            self.default_options = getattr(base_options, 'default_options')
            if not self.default_options:
                self.default_options = {}

    def __str__(self):
        return str({
            'options': self.options,
            'default_options': self.default_options})

    @property
    def boost_build_defines(self):
        return []

    @property
    def boost_build_options(self):
        return {}

    @property
    def boost_build_requires(self):
        return []

    def requirements(self):
        pass

    def build_requirements(self):
        pass

    def config_options(self):
        pass

    def package_info(self):
        pass

    def source(self):
        pass

    def package_id(self):
        pass

    def package(self):
        pass

    def build_lib(self, lib):
        pass


class BoostConanMixin_Shared(BoostConanMixin):
    '''
    Mixin to define `shared` package option.
    '''

    options = {
        'shared': [False, True]
    }
    default_options = {
        'shared': False
    }

    @property
    def matches(self):
        '''
        Add the `shared` option when there are libraries to build. I.e. not
        when we have all header only libs.
        '''
        return len(self.conanfile.boost_libs_to_build) > 0


boost_conan_mixins.append(BoostConanMixin_Shared)


class BoostConanMixin_UseICU(BoostConanMixin):
    '''
    This adds a `use_icu` option for packages where ICU can be used.
    '''

    options = {
        "use_icu": [True, False]
    }
    default_options = {
        "use_icu": False
    }

    @property
    def matches(self):
        '''
        This matches when it's the locale or regex libraries. Because the
        libraries could be: an alias package, in a cycle group, or standalone
        we need to check both the set of libraries in the package and the
        package itself.
        '''
        return 'locale' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'locale' or\
            'regex' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'regex'

    @property
    def boost_build_options(self):
        if 'locale' in self.conanfile.boost_libs:
            # These are the B2 fatures that Boost Locale uses to optionally
            # build with ICU.
            if self.conanfile.options.use_icu:
                return {
                    "boost.locale.iconv": "off",
                    "boost.locale.icu": "on"
                }
            else:
                return {
                    "boost.locale.iconv": "on",
                    "boost.locale.icu": "off"
                }
        return {}

    def requirements(self):
        if self.conanfile.options.use_icu:
            # We use the Conan ICU package when enabled.
            self.conanfile.requires("icu/63.1@bincrafters/stable")

    def package_info(self):
        if 'locale' in self.conanfile.boost_libs:
            if self.conanfile.options.use_icu:
                # Boost Locale consumers need to also define a specific
                # preprocess symbol to tell the header code they want ICU
                # features.
                self.conanfile.cpp_info.defines.append(
                    "BOOST_LOCALE_WITH_ICU=1")
            elif self.conanfile.settings.os == "Macos":
                # On macOS Boost Locale uses the system iconv library.
                self.conanfile.cpp_info.libs.append("iconv")


boost_conan_mixins.append(BoostConanMixin_UseICU)


class BoostConanMixin_WithBoostPython(BoostConanMixin):
    '''
    Adds a `with_boost_python` option to control optional use of Boost Python.
    '''

    options = {
        'with_boost_python': [True, False]
    }

    default_options = {
        'with_boost_python': False
    }

    @property
    def matches(self):
        '''
        This mixing maches for the Boost MPI library.
        '''
        return 'mpi' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'mpi'

    def requirements(self):
        if self.conanfile.options.with_boost_python:
            self.conanfile.requires(
                "boost_python/{ver}@{user}/{channel}".format(
                    ver=self.conanfile.version,
                    user=self.conanfile.user,
                    channel=self.conanfile.channel
                ))

    def package_info(self):
        if self.conanfile.options.with_boost_python:
            # We unpin the python version of the dependency so that
            # user specification overrides the dependency.
            self.conanfile.info.options["boost_python"].python_version = "any"


boost_conan_mixins.append(BoostConanMixin_WithBoostPython)


class BoostConanMixin_MPILib(BoostConanMixin):
    '''
    THis mixin adds the requirements and setup for using and MPI framework.
    '''

    @property
    def matches(self):
        return 'mpi' in self.conanfile.boost_libs_to_build

    def build_requirements(self):
        if not tools.os_info.is_windows:
            self.conanfile.build_requires("openmpi/3.0.0@bincrafters/stable")


boost_conan_mixins.append(BoostConanMixin_MPILib)


class BoostConanMixin_Iostreams(BoostConanMixin):
    '''
    Specifies settings for "iostreams" library. Needed as it's part of a cycle.
    '''

    # TODO: This could be separated into individual mixins.

    options = {
        "use_bzip2": [True, False],
        "use_lzma": [True, False],
        "use_zlib": [True, False],
        "use_zstd": [True, False]
    }
    default_options = {
        'use_bzip2': True,
        'use_lzma': True,
        'use_zlib': True,
        'use_zstd': True
    }

    @property
    def matches(self):
        return 'iostreams' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'iostreams'

    @property
    def boost_build_defines(self):
        if self.conanfile.options.use_lzma:
            return ["LZMA_API_STATIC"]
        else:
            return []

    def requirements(self):
        if self.conanfile.options.use_bzip2:
            self.conanfile.requires("bzip2/1.0.6@conan/stable")
        if self.conanfile.options.use_zlib:
            self.conanfile.requires("zlib/1.2.11@conan/stable")
        if self.conanfile.options.use_lzma:
            self.conanfile.requires("lzma/5.2.4@bincrafters/stable")
        if self.conanfile.options.use_zstd:
            self.conanfile.requires("zstd/1.4.3@")

    def package_info(self):
        if self.conanfile.options.use_bzip2:
            self.conanfile.cpp_info.defines.append(
                "BOOST_IOSTREAMS_USE_BZIP2=1")
        if self.conanfile.options.use_zlib:
            self.conanfile.cpp_info.defines.append(
                "BOOST_IOSTREAMS_USE_ZLIB=1")
        if self.conanfile.options.use_lzma:
            self.conanfile.cpp_info.defines.append(
                "BOOST_IOSTREAMS_USE_LZMA=1")
        if self.conanfile.options.use_zstd:
            self.conanfile.cpp_info.defines.append(
                "BOOST_IOSTREAMS_USE_ZSTD=1")
        if self.conanfile.options.shared:
            self.conanfile.cpp_info.defines.append(
                "BOOST_IOSTREAMS_DYN_LINK=1")


boost_conan_mixins.append(BoostConanMixin_Iostreams)


class BoostConanMixin_Thread(BoostConanMixin):
    '''
    Specifies settings for "thread" library. Needed as it's part of a cycle.
    '''

    options = {
        "threadapi": ['default', 'win32', 'pthread']
    }
    default_options = {
        'threadapi': 'default'
    }

    @property
    def matches(self):
        return 'thread' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'thread'

    def package_info(self):
        '''
        Consumers need to link to an additional system provided native
        threading API.
        '''
        if self.conanfile.settings.os != "Windows":
            self.conanfile.cpp_info.libs.append("pthread")
        elif self.conanfile.settings.os == "Linux":
            self.conanfile.cpp_info.libs.append("rt")


boost_conan_mixins.append(BoostConanMixin_Thread)


class BoostConanMixin_PythonDevConfig(BoostConanMixin):
    '''
    Configures using `python_dev_config` for libraries that provide some
    interface to Python.
    '''

    options = {
        "python_version": [
            None, '2.2', '2.3', '2.4', '2.5', '2.6', '2.7', '3.0', '3.1',
            '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9']
    }

    @property
    def matches(self):
        return 'python' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'python'

    def config_options(self):
        if 'python_version' in self.options:
            # The user specified version must match the dependency.
            if self.conanfile.options.python_version and \
                self.conanfile.options.python_version \
                    != self.conanfile.deps_user_info[
                        'python_dev_config'].python_version:
                raise Exception(
                    "Python version does not match with configured python " +
                    "dev, expected %s but got %s." % (
                        self.conanfile.options.python_version,
                        self.conanfile.deps_user_info[
                            'python_dev_config'].python_version))

    def requirements(self):
        self.conanfile.requires("python_dev_config/0.6@bincrafters/stable")

    def package_info(self):
        # TODO: This probably belongs in separate BPL mixin.
        if self.conanfile.options.shared:
            self.conanfile.cpp_info.defines.append('BOOST_PYTHON_DYNAMIC_LIB')
        else:
            self.conanfile.cpp_info.defines.append('BOOST_PYTHON_STATIC_LIB')

    def package_id(self):
        self.conanfile.info.options.python_version \
            = "python-" + str(self.conanfile.options.python_version)


boost_conan_mixins.append(BoostConanMixin_PythonDevConfig)


class BoostConanMixin_Stacktrace(BoostConanMixin):
    '''
    Specifies settings for "stacktrace" library.
    '''

    @property
    def matches(self):
        return 'stacktrace' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'stacktrace'

    def package_info(self):
        self.conanfile.cpp_info.defines.append(
            "BOOST_STACKTRACE_GNU_SOURCE_NOT_REQUIRED=1")


boost_conan_mixins.append(BoostConanMixin_Stacktrace)


class BoostConanMixin_Test(BoostConanMixin):
    '''
    Specifies settings for "test" library.
    '''

    @property
    def matches(self):
        return 'test' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'test'

    @property
    def boost_build_requires(self):
        return ["predef"]

    def package_info(self):
        self.conanfile.cpp_info.libs = [
            x
            for x in self.conanfile.cpp_info.libs
            if x.find('exec_monitor') < 0]


boost_conan_mixins.append(BoostConanMixin_Test)


class BoostConanMixin_Predef(BoostConanMixin):
    '''
    Specifies settings for "predef" library.
    '''

    @property
    def matches(self):
        return self.conanfile.boost_name == 'predef'

    def package(self):
        for subdir in ("check", "tools"):
            src_dir = os.path.join('predef', subdir)
            self.conanfile.copy(
                pattern="*.jam",
                dst=os.path.join('predef', "lib", subdir),
                src=src_dir)
            self.conanfile.copy(
                pattern="*.c*",
                dst=os.path.join('predef', "lib", subdir),
                src=src_dir)
            self.conanfile.copy(
                pattern="*.m*",
                dst=os.path.join('predef', "lib", subdir),
                src=src_dir)


boost_conan_mixins.append(BoostConanMixin_Predef)


class BoostConanMixin_Context(BoostConanMixin):
    '''
    Specifies settings for "context" library.
    '''

    @property
    def matches(self):
        return self.conanfile.boost_name == 'context'

    @property
    def boost_build_options(self):
        return {
            "binary-format": self.b2_binary_format,
            "abi": self.b2_abi
        }

    @property
    def b2_binary_format(self):
        if self.conanfile.settings.os == "iOS" or self.conanfile.settings.os == "Macos":
            return "mach-o"
        elif self.conanfile.settings.os == "Android" or self.conanfile.settings.os == "Linux":
            return "elf"
        elif self.conanfile.settings.os == "Windows":
            return "pe"
        else:
            return ""

    @property
    def b2_abi(self):
        if str(self.conanfile.settings.arch).startswith('x86'):
            if self.conanfile.settings.os == "Windows":
                return "ms"
            else:
                return "sysv"
        elif str(self.conanfile.settings.arch).startswith('ppc'):
            return "sysv"
        elif str(self.conanfile.settings.arch).startswith('arm'):
            return "aapcs"
        else:
            return ""

    def build_lib(self, lib):
        if lib == 'context':
            jam_content = """
    import feature ;
    feature.feature segmented-stacks : on : optional propagated composite ;
    feature.compose <segmented-stacks>on : <define>BOOST_USE_SEGMENTED_STACKS ;
    """
            tools.save(
                os.path.join(
                    self.conanfile.build_folder, "context", "lib", "jamroot.jam"),
                jam_content,
                append=True)


boost_conan_mixins.append(BoostConanMixin_Context)


class BoostConanMixin_Config(BoostConanMixin):
    '''
    Specifies settings for "config" library.
    '''

    @property
    def matches(self):
        return self.conanfile.boost_name == 'config'

    def package(self):
        src_dir = os.path.join("config", "checks")
        self.conanfile.copy(
            pattern="*.jam",
            dst=os.path.join("config", "lib", "checks"),
            src=src_dir)
        self.conanfile.copy(
            pattern="*.cpp",
            dst=os.path.join("config", "lib", "checks"),
            src=src_dir)
        self.conanfile.copy(
            pattern="Jamfile*",
            dst=os.path.join("config", "lib", "checks"),
            src=src_dir)


boost_conan_mixins.append(BoostConanMixin_Config)


class BoostConanMixin_Log(BoostConanMixin):
    '''
    Specifies settings for "log" library.
    '''

    @property
    def matches(self):
        return 'log' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'log'

    @property
    def boost_build_requires(self):
        return ["align", "asio", "interprocess"]

    def package_info(self):
        if self.conanfile.options.shared:
            self.conanfile.cpp_info.defines.append("BOOST_LOG_DYN_LINK=1")
            self.conanfile.cpp_info.defines.append("BOOST_LOG_SETUP_DYN_LINK=1")


boost_conan_mixins.append(BoostConanMixin_Log)


class BoostConanMixin_Interprocess(BoostConanMixin):
    '''
    Specifies settings for "interprocess" library.
    '''

    @property
    def matches(self):
        return 'interprocess' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'interprocess'

    def package_info(self):
        if self.conanfile.settings.os == "Linux":
            self.conanfile.cpp_info.libs.append("rt")


boost_conan_mixins.append(BoostConanMixin_Interprocess)


class BoostConanMixin_ParameterPython(BoostConanMixin):
    '''
    Specifies settings for "parameter_python" library.
    '''

    @property
    def matches(self):
        return 'parameter_python' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'parameter_python'

    def package_info(self):
        self.conanfile.info.options["boost_python"].python_version = "any"
        if self.conanfile.settings.os == "Linux":
            self.conanfile.cpp_info.libs.append("rt")


boost_conan_mixins.append(BoostConanMixin_ParameterPython)


class BoostConanMixin_Uuid(BoostConanMixin):
    '''
    Specifies settings for "uuid" library.
    '''

    @property
    def matches(self):
        return 'uuid' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'uuid'

    def package_info(self):
        if self.conanfile.settings.os == "Windows":
            self.conanfile.cpp_info.libs.append("Bcrypt")


boost_conan_mixins.append(BoostConanMixin_Uuid)


class BoostConanMixin_ProgramOptions(BoostConanMixin):
    '''
    Specifies settings for "program_options" library.
    '''

    @property
    def matches(self):
        return 'program_options' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'program_options'

    @property
    def boost_build_defines(self):
        return ["BOOST_PROGRAM_OPTIONS_DYN_LINK=1"]


boost_conan_mixins.append(BoostConanMixin_ProgramOptions)


class BoostConanMixin_Contract(BoostConanMixin):
    '''
    Specifies settings for "contract" library.
    '''

    @property
    def matches(self):
        return 'contract' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'contract'

    @property
    def boost_build_requires(self):
        return ["system"]


boost_conan_mixins.append(BoostConanMixin_Contract)


class BoostConanMixin_Timer(BoostConanMixin):
    '''
    Specifies settings for "timer" library.
    '''

    @property
    def matches(self):
        return 'timer' in self.conanfile.boost_libs or\
            self.conanfile.boost_name == 'timer'

    @property
    def boost_build_requires(self):
        return ["io"]


boost_conan_mixins.append(BoostConanMixin_Timer)
