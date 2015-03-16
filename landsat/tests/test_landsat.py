# Landsat Util
# License: CC0 1.0 Universal

"""Tests for landsat"""

import sys
import errno
import shutil
import unittest
import subprocess
from tempfile import mkdtemp
from os.path import join, abspath, dirname

try:
    import landsat.landsat as landsat
except ImportError:
    sys.path.append(abspath(join(dirname(__file__), '../landsat')))
    import landsat.landsat as landsat


class TestLandsat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_folder = mkdtemp()
        cls.base_dir = abspath(dirname(__file__))
        cls.landsat_image = join(cls.base_dir, 'samples', 'test.tar.bz2')
        cls.parser = landsat.args_options()

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.temp_folder)
            shutil.rmtree(join(cls.base_dir, 'samples', 'test'))
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def system_exit(self, args, code):
        try:
            landsat.main(self.parser.parse_args(args))
        except SystemExit as e:
            self.assertEqual(e.code, code)

    def test_incorrect_date(self):
        """ Test search with incorrect date input """

        args = ['search', '--start', 'berlin', '--end', 'january 10 2014']

        self.system_exit(args, 1)

    def test_too_many_results(self):
        """ Test when search return too many results """

        args = ['search', '--cloud', '100', '-p', '205,022,206,022,204,022']

        self.system_exit(args, 1)

    def test_search_pr_correct(self):
        """Test Path Row search with correct input"""
        args = ['search', '--start', 'january 1 2013', '--end',
                'january 10 2014', '-p', '008,008']

        self.system_exit(args, 0)

    def test_search_lat_lon(self):
        """Test Latitude Longitude search with correct input"""
        args = ['search', '--start', 'may 01 2013', '--end', 'may 08 2013',
                '--lat', '38.9107203', '--lon', '-77.0290116']

        self.system_exit(args, 0)

    def test_search_pr_wrong_input(self):
        """Test Path Row search with incorrect input"""
        args = ['search', '-p', 'what?']

        self.system_exit(args, 1)

    def test_download_correct(self):
        """Test download command with correct input"""
        args = ['download', 'LC80010092015051LGN00', '-b', '11,', '-d', self.temp_folder]

        self.system_exit(args, 0)

    def test_download_incorrect(self):
        """Test download command with incorrect input"""
        args = ['download', 'LT813600']

        self.system_exit(args, 1)

    def test_download_process_continuous(self):
        """Test download and process commands together"""

        args = ['download', 'LC80010092015051LGN00', '-b', '432', '-d', self.temp_folder, '-p']
        self.system_exit(args, 0)

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

    def check_command_line(self):
        """ Check if the commandline performs correctly """

        self.assertEqual(subprocess.call(['python', join(self.base_dir, '../landsat.py'), '-h']), 0)


if __name__ == '__main__':
    unittest.main()
