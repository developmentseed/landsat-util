# Landsat Util
# License: CC0 1.0 Universal

"""Tests for image processing"""

from os.path import join, abspath, dirname, exists
import errno
import shutil
import unittest
from tempfile import mkdtemp

from landsat.image import Simple, PanSharpen
from landsat.ndvi import NDVI, NDVIWithManualColorMap


class TestProcess(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = abspath(dirname(__file__))
        cls.temp_folder = mkdtemp()
        cls.landsat_image = join(cls.base_dir, 'samples/test.tar.bz2')

    @classmethod
    def tearDownClass(cls):

        try:
            shutil.rmtree(cls.temp_folder)
            shutil.rmtree(join(cls.base_dir, 'samples', 'test'))
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def test_simple_no_bands(self):

        p = Simple(path=self.landsat_image, dst_path=self.temp_folder)
        p.run()
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_432.TIF')))

    def test_simple_with_bands(self):

        p = Simple(path=self.landsat_image, bands=[1, 2, 3], dst_path=self.temp_folder)
        p.run()
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_123.TIF')))

    def test_simple_with_zip_file(self):

        p = Simple(path=self.landsat_image, dst_path=self.temp_folder)

        # test from an unzip file
        self.path = join(self.base_dir, 'samples', 'test')
        p.run()
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_432.TIF')))

    def test_pansharpen(self):
        # test with pansharpen

        p = PanSharpen(path=self.landsat_image, bands=[4, 3, 2], dst_path=self.temp_folder)
        p.run()
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_bands_432_pan.TIF')))

    def test_ndvi(self):

        p = NDVI(path=self.landsat_image, dst_path=self.temp_folder)
        print p.run()
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_NDVI.TIF')))

    def test_ndvi_with_manual_colormap(self):

        p = NDVIWithManualColorMap(path=self.landsat_image, dst_path=self.temp_folder)
        print p.run()
        self.assertTrue(exists(join(self.temp_folder, 'test', 'test_NDVI.TIF')))
