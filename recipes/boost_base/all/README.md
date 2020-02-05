## Boost Modular Packages

This is the base class, as a python requires package, for the Boost modular
packages. It contains all the packaging logic for all supported
versions of Boost.

### Contents

* `src/data` -- Contains the generated information for the Boost packages as
    JSON data for each version.
* `src/script` -- Contains generation and build scripts for creating and
    maintaining the packages as one development unit.
    * `package_data_gen.py` -- Generates the
        `package-data-boost-<version>.json` data.
    * `create_all.py` -- Invokes `conan create ...` for each package in
        dependency order.
* `src/template` -- Template files used during the Conan packaging and
    building processing.
* `src/tet_package` -- Test packages for each of the Boost recipes that get
    copied when generating them.

### Release

Generating the packages for a modular Boost release is complex. But hopefully
the scripts here make it as simple as possible. But be warned; this is a
continuing work in progress.

#### Base Package

This package contains scripts to automate the Boost libraries data and other
utilities to deal with the numerous, and growing, Boost modular packages.

```
cd <cci>/recipes/boost_base/all
```

#### Release Data

Next we need to generate the package data that specifies the setup and
dependencies for the particular Boost release. For that we need to a few
source pieces and scripts. Before we proceed with this there are two
dependencies we need to account for:

1. Python 3
2. Boost Library Statistics, aka `bls`, utility Python package.

All the scripts here and in `bls` use Python version 3. Hence you will
need to install that to continue. The `bls` package can be installed
directly from the GitHub repo with `pip`:

```
pip3 install --user --upgrade https://github.com/grafikrobot/boost_lib_stats/archive/master.zip
```

We can now use the `package_data_gen.py` script to do all the heavy work needed
to obtain Boost libraries and to inspect them to generate the package
dependency information.

```
./src/script/package_data_gen.py ++version=1.71.0
```

That will download Boost from GitHub, build the introspection tools, and
end up generating a `./src/data/package-data-boost-1.71.0.json`
file.

The base package also contains some global per-release configurable data in
the `<cci>/recipes/boost_base/all/conandata.yml` file. For a new release you
will need to add an entry similar to:

```
"1.71.0":
  b2_version: 4.0.1
```

In the `boost_info` entry of the data.

#### Generating Boost Packages

The Boost packages will be created, or updated, in the `<cci>/recipes`
directory by default.

```
cd <cci>/recipes
```

We now use the `make_conan_boost.py` script in the `boost_base` recipe to
generate, or update, the new Boost packages.

```
./boost_base/all/src/script/make_conan_boost.py ++++base-ref=2.1.0@bincrafters/testing ++version=1.71.0
```

#### Testing Packages

It's impractical to test the numerous Boost packages manually, one by one.
Especially since we need to generate all the dependencies of a package.
Instead we can use the `create_all.py` script to automate this step. The script
will run through the packages available in dependency order and call
`conan create . <package>/<version>@<user>/<channel>` minimizing the amount of
package database re-scanning and exports. To use invoke like this:

```
./boost_base/all/script/create_all.py ++version=1.70.0 ++user=bincrafters ++channel=testing ++repo-dir=.
```

Which will locally build and test the packages with the default settings and
options. You can check with other settings and options by adding options
for them as regular `--` options. For example to test shared library building:

```
./boost_base/all/script/create_all.py ++version=1.70.0 ++user=bincrafters ++channel=testing ++repo-dir=. "--options=*:shared=True"
```
