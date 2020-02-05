from conans import ConanFile


class BoostMplConan(ConanFile):
    name = "boost_mpl"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
