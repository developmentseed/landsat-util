# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

"""Tests for landsat"""

import os
import sys
import unittest

try:
    import landsat.landsat as landsat
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../landsat')))
    import landsat


class TestLandsat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.dirname(__file__))
        cls.shapefile = cls.base_dir + '/samples/test_shapefile.shp'
        cls.parser = landsat.args_options()

    def test_search_pr_correct(self):
        # Correct search
        args = ['search', '--onlysearch', 'pr', '008', '008']

        with self.assertRaises(SystemExit) as cm:
            landsat.main(self.parser.parse_args(args))

        self.assertEqual(cm.exception.code, 0)

    def test_search_pr_wrong_input(self):
        args = ['search', '--onlysearch', 'pr', 'what?']

        with self.assertRaises(SystemExit) as cm:
            landsat.main(self.parser.parse_args(args))

        self.assertNotEqual(cm.exception.code, 0)

    def test_search_shapefile_correct(self):
        args = ['search', '--onlysearch', 'shapefile', self.shapefile]

        with self.assertRaises(SystemExit) as cm:
            landsat.main(self.parser.parse_args(args))

        self.assertEqual(cm.exception.code, 0)

    def test_search_shapefile_incorrect(self):
        args = ['search', '--onlysearch', 'shapefile', 'whatever']

        with self.assertRaises(Exception) as cm:
            landsat.main(self.parser.parse_args(args))

        self.assertEqual(cm.exception.args[0],
                         'Invalid Argument. Please try again!')



if __name__ == '__main__':
    unittest.main()

