# Landsat Util
# License: CC0 1.0 Universal

"""Tests for downloader"""

import os
import sys
import errno
import shutil
import unittest
from tempfile import mkdtemp

try:
    from landsat.downloader import Downloader
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../landsat')))
    from downloader import Downloader


class TestDownloader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = Downloader()
        cls.temp_folder = mkdtemp()
        cls.scene = 'LT81360082013127LGN01'
        cls.scene_s3 = 'LC80010092015051LGN00'
        cls.scene_size = 59204484

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.temp_folder)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def assertSize(self, url, path):
        remote_size = self.d.get_remote_file_size(url)
        download_size = os.path.getsize(path)

        self.assertEqual(remote_size, download_size)

    def test_download(self):
        sat = self.d.scene_interpreter(self.scene)
        url = self.d.google_storage_url(sat)
        self.d.download_dir = self.temp_folder

        # download one list
        self.d.download([self.scene])
        self.assertSize(url, os.path.join(self.temp_folder, self.scene + '.tar.bz'))

        # pass string instead of list
        self.assertRaises(Exception, self.d.download, self.scene)

        # pass multiple sceneIDs
        self.d.download([self.scene, self.scene])
        self.assertSize(url, os.path.join(self.temp_folder, self.scene + '.tar.bz'))

        # pass band along with sceneID
        self.d.download([self.scene_s3], bands=[11])
        filename = '%s_B11.TIF' % self.scene_s3
        sat = self.d.scene_interpreter(self.scene_s3)
        url = self.d.amazon_s3_url(sat, filename)

        self.assertSize(url, os.path.join(self.temp_folder, self.scene_s3, filename))

        # pass band as string
        self.assertRaises(Exception, self.d.download, self.scene, 4)

    def test_google_storage(self):
        sat = self.d.scene_interpreter(self.scene)
        url = self.d.google_storage_url(sat)
        self.d.google_storage(self.scene, self.temp_folder)

        self.assertSize(url, os.path.join(self.temp_folder, self.scene + '.tar.bz'))

    def test_amazon_s3(self):
        scene = self.scene_s3
        sat = self.d.scene_interpreter(scene)
        filename = '%s_B11.TIF' % scene
        url = self.d.amazon_s3_url(sat, filename)

        self.d.amazon_s3(scene, 11, self.temp_folder)

        self.assertSize(url, os.path.join(self.temp_folder, filename))

    def test_fetch(self):
        sat = self.d.scene_interpreter(self.scene)
        url = self.d.google_storage_url(sat)

        # download
        self.d.fetch(url, self.temp_folder, self.scene)
        self.assertSize(url, os.path.join(self.temp_folder, self.scene + '.tar.bz'))

    def test_remote_file_size(self):

        url = self.d.google_storage_url(self.d.scene_interpreter(self.scene))
        size = self.d.get_remote_file_size(url)

        self.assertEqual(self.scene_size, size)

    def test_google_storage_url(self):
        sat = self.d.scene_interpreter(self.scene)

        string = self.d.google_storage_url(sat)
        expect = 'https://storage.googleapis.com/earthengine-public/landsat/L8/136/008/LT81360082013127LGN01.tar.bz'
        self.assertEqual(expect, string)

    def test_amazon_s3_url(self):
        sat = self.d.scene_interpreter(self.scene)
        filename = '%s_B11.TIF' % self.scene

        string = self.d.amazon_s3_url(sat, filename)
        expect = 'https://landsat-pds.s3.amazonaws.com/L8/136/008/LT81360082013127LGN01/LT81360082013127LGN01_B11.TIF'

        self.assertEqual(expect, string)

    def test_remote_file_exist(self):
        # Test a url that doesn't exist
        self.assertTrue(self.d.remote_file_exists('https://landsat-pds.s3.amazonaws.com/L8/003/017/LC80030172015001L'
                                                  'GN00/LC80030172015001LGN00_B6.TIF'))

        # Test a url that exist
        self.assertFalse(self.d.remote_file_exists('https://landsat-pds.s3.amazonaws.com/L8/003/017/LC80030172015001L'
                                                   'GN00/LC80030172015001LGN00_B34.TIF'))

    def test_scene_interpreter(self):
        # Test with correct input
        scene = 'LC80030172015001LGN00'
        ouput = self.d.scene_interpreter(scene)
        self.assertEqual({'path': '003', 'row': '017', 'sat': 'L8', 'scene': scene}, ouput)

        # Test with incorrect input
        self.assertRaises(Exception, self.d.scene_interpreter, 'LC80030172015001LGN')

if __name__ == '__main__':
    unittest.main()
