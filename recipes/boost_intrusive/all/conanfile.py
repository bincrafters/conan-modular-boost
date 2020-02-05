from conans import ConanFile


class BoostIntrusiveConan(ConanFile):
    name = "boost_intrusive"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
