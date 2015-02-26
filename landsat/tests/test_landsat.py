# Landsat Util
# License: CC0 1.0 Universal

"""Tests for landsat"""

import os
import sys
import unittest
import subprocess

try:
    import landsat.landsat as landsat
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../../landsat')))
    from landsat import landsat


class TestLandsat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.dirname(__file__))
        cls.shapefile = cls.base_dir + '/samples/test_shapefile.shp'
        cls.landsat_image = cls.base_dir + '/samples/test.tar.bz2'
        cls.parser = landsat.args_options()

    def system_exit(self, args, code):
        try:
            landsat.main(self.parser.parse_args(args))
        except SystemExit as e:
            print e.message
            self.assertEqual(e.code, code)

    def test_incorrect_date(self):
        """ Test search with incorrect date input """

        args = ['search', '--start', 'berlin', '--end', 'january 10 2014', 'pr', '008', '008']

        self.system_exit(args, 1)

    def test_few_arguments(self):
        """ Test the few arguments error """

        args = ['search', '--start', 'berlin', '--end', 'january 10 2014']

        self.system_exit(args, 2)

    def test_too_many_results(self):
        """ Test when search return too many results """

        args = ['search', '--cloud', '100', 'pr', '205', '022', '206', '022', '204', '022']

        self.system_exit(args, 1)

    def test_search_pr_correct(self):
        """Test Path Row search with correct input"""
        args = ['search', '--start', 'january 1 2013', '--end',
                'january 10 2014', 'pr', '008', '008']

        self.system_exit(args, 0)

    def test_search_pr_with_download(self):
        """Test Path Row search with correct input and download"""
        args = ['search', '--start', 'may 06 2013', '--end', 'may 08 2013', '-d', 'pr', '136', '008']

        self.system_exit(args, 0)

    def test_search_pr_wrong_input(self):
        """Test Path Row search with incorrect input"""
        args = ['search', 'pr', 'what?']

        self.system_exit(args, 2)

    def test_search_shapefile_correct(self):
        """Test shapefile search with correct input"""
        args = ['search', 'shapefile', self.shapefile]

        self.system_exit(args, 0)

    def test_search_shapefile_incorrect(self):
        """Test shapefile search with incorrect input"""
        args = ['search', 'shapefile', 'whatever']

        self.system_exit(args, 1)

    def test_search_country_correct(self):
        """Test shapefile search with correct input"""
        args = ['search', 'country', 'Nauru']

        self.system_exit(args, 0)

    def test_download_correct(self):
        """Test download command with correct input"""
        args = ['download', 'LT81360082013127LGN01']

        self.system_exit(args, 0)

    def test_download_incorrect(self):
        """Test download command with incorrect input"""
        args = ['download', 'LT813600']

        self.system_exit(args, 1)

    def test_process_correct(self):
        """Test process command with correct input"""
        args = ['process', self.landsat_image]

        self.system_exit(args, 0)

    def test_process_correct_pansharpen(self):
        """Test process command with correct input and pansharpening"""
        args = ['process', '--pansharpen', self.landsat_image]

        self.system_exit(args, 0)

    def test_process_incorrect(self):
        """Test process command with incorrect input"""
        args = ['process', 'whatever']

        self.system_exit(args, 1)

    def check_package_installed(self):
        """ Checks if the package is installed """
        self.assertTrue(landsat.package_installed('python'))
        self.assertFalse(landsat.package_installed('whateverpackage'))

    def check_command_line(self):
        """ Check if the commandline performs correctly """

        self.assertEqual(subprocess.call(['python', os.path.join(self.base_dir, '../landsat.py'), '-h']), 0)


if __name__ == '__main__':
    unittest.main()
