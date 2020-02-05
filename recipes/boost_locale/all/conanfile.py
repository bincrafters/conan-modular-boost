from conans import ConanFile


class BoostLocaleConan(ConanFile):
    name = "boost_locale"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
