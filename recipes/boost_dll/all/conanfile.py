from conans import ConanFile


class BoostDllConan(ConanFile):
    name = "boost_dll"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
