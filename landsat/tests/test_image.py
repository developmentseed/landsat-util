# Landsat Util
# License: CC0 1.0 Universal

"""Tests for image processing"""

from os.path import join, abspath, dirname, exists
import sys
import errno
import shutil
import unittest
from tempfile import mkdtemp

try:
    from landsat.image import Process
except ImportError:
    sys.path.append(abspath(join(dirname(__file__), '../landsat')))
    from image import Process


class TestProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = abspath(dirname(__file__))
        cls.temp_folder = mkdtemp()
        cls.landsat_image = join(cls.base_dir, 'samples/test.tar.bz2')
        cls.p = Process(path=cls.landsat_image, dst_path=cls.temp_folder)

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.temp_folder)
            shutil.rmtree(join(cls.base_dir, 'samples', 'test'))
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def test_run(self):

        # test with no bands
        self.p.run(False)
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_432.TIF')))

        # test with bands
        self.p.bands = [1, 2, 3]
        self.p.run(False)
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_123.TIF')))

        # test with pansharpen
        self.p.bands = [4, 3, 2]
        self.p.run()
        print self.temp_folder
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_432_pan.TIF')))

        # test from an unzip file
        self.path = join(self.base_dir, 'samples', 'test')
        self.p.run(False)
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_432.TIF')))
