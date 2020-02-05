from conans import ConanFile


class BoostPolygonConan(ConanFile):
    name = "boost_polygon"
    short_paths = True
    python_requires = "boost_base/2.1.0@bincrafters/testing"
    python_requires_extend = "boost_base.BoostBaseConan"
