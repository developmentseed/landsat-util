# Landsat Util
# License: CC0 1.0 Universal

"""Tests for clipper_helper"""

import os
import sys
import unittest

try:
    from landsat.clipper_helper import Clipper
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../landsat')))
    from clipper_helper import Clipper


class TestClipperHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c = Clipper()
        cls.base_dir = os.path.abspath(os.path.dirname(__file__))
        cls.shapefile = cls.base_dir + '/samples/test_shapefile.shp'

    def test_shapefile(self):
        # Test with correct shapefile
        self.assertEqual([[u'009', u'045'], [u'008', u'045']],
                         self.c.shapefile(self.shapefile))

    def test_country(self):
        # Test output of a known country
        self.assertEqual([['145', u'057'], ['145', u'058']],
                         self.c.country('Maldives'))


if __name__ == '__main__':
    unittest.main()
