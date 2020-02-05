from conans import ConanFile


class BoostContextConan(ConanFile):
    name = "boost_context"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
