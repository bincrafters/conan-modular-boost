from conans import ConanFile


class BoostVmdConan(ConanFile):
    name = "boost_vmd"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
