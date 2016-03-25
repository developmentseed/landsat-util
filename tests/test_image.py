# Landsat Util
# License: CC0 1.0 Universal

"""Tests for image processing"""

from os.path import join, abspath, dirname, exists
import errno
import shutil
import unittest
from tempfile import mkdtemp

import rasterio
from rasterio.warp import transform_bounds

from landsat.image import Simple, PanSharpen
from landsat.ndvi import NDVI, NDVIWithManualColorMap


def get_bounds(path):
    """ Retrun bounds in WGS84 system """

    with rasterio.drivers():
        src = rasterio.open(path)

        return transform_bounds(
                    src.crs,
                    {'init': 'EPSG:4326'},
                    *src.bounds)


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
        self.assertTrue(exists(p.run()))

    def test_simple_with_bands(self):

        p = Simple(path=self.landsat_image, bands=[1, 2, 3], dst_path=self.temp_folder)
        self.assertTrue(exists(p.run()))

    def test_simple_with_clip(self):

        bounds = [-87.48138427734375, 30.700515832683923, -87.43331909179688, 30.739475058679485]
        p = Simple(path=self.landsat_image, bands=[1, 2, 3], dst_path=self.temp_folder,
                   bounds=bounds)
        path = p.run()
        self.assertTrue(exists(path))
        for val, exp in zip(get_bounds(path), bounds):
            self.assertAlmostEqual(val, exp, 2)

    def test_simple_with_intersecting_bounds_clip(self):

        bounds = [-87.520515832683923, 30.700515832683923, -87.43331909179688, 30.739475058679485]
        expected_bounds = [-87.49691403528307, 30.700515832683923, -87.43331909179688, 30.739475058679485]
        p = Simple(path=self.landsat_image, bands=[1, 2, 3], dst_path=self.temp_folder,
                   bounds=bounds)
        path = p.run()
        self.assertTrue(exists(path))
        for val, exp in zip(get_bounds(path), expected_bounds):
            self.assertAlmostEqual(val, exp, 2)

    def test_simple_with_out_of_bounds_clip(self):

        bounds = [-87.66197204589844, 30.732392734006083, -87.57545471191406, 30.806731169315675]
        expected_bounds = [-87.49691403528307, 30.646646570857722, -87.29976764207227, 30.810617911193567]
        p = Simple(path=self.landsat_image, bands=[1, 2, 3], dst_path=self.temp_folder,
                   bounds=bounds)
        path = p.run()
        self.assertTrue(exists(path))
        for val, exp in zip(get_bounds(path), expected_bounds):
            self.assertAlmostEqual(val, exp, 2)

    def test_simple_with_zip_file(self):

        p = Simple(path=self.landsat_image, dst_path=self.temp_folder)

        # test from an unzip file
        self.path = join(self.base_dir, 'samples', 'test')
        self.assertTrue(exists(p.run()))

    def test_pansharpen(self):
        p = PanSharpen(path=self.landsat_image, bands=[4, 3, 2], dst_path=self.temp_folder)
        self.assertTrue(exists(p.run()))

    def test_pansharpen_with_clip(self):
        """ test with pansharpen and clipping """

        bounds = [-87.48138427734375, 30.700515832683923, -87.43331909179688, 30.739475058679485]
        p = PanSharpen(path=self.landsat_image, bands=[4, 3, 2], dst_path=self.temp_folder,
                       bounds=bounds)
        path = p.run()
        self.assertTrue(exists(path))
        for val, exp in zip(get_bounds(path), bounds):
            self.assertAlmostEqual(val, exp, 2)

    def test_ndvi(self):

        p = NDVI(path=self.landsat_image, dst_path=self.temp_folder)
        self.assertTrue(exists(p.run()))

    def test_ndvi_with_clip(self):

        bounds = [-87.48138427734375, 30.700515832683923, -87.43331909179688, 30.739475058679485]
        p = NDVI(path=self.landsat_image, dst_path=self.temp_folder,
                 bounds=bounds)
        path = p.run()
        self.assertTrue(exists(path))
        for val, exp in zip(get_bounds(path), bounds):
            self.assertAlmostEqual(val, exp, 2)

    def test_ndvi_with_manual_colormap(self):

        p = NDVIWithManualColorMap(path=self.landsat_image, dst_path=self.temp_folder)
        self.assertTrue(exists(p.run()))
