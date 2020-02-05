from conans import ConanFile


class TestPackageConan(ConanFile):
    name = "boost_test_package_conan"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"

    def test(self):
        pass
