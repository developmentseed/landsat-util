# Landsat Util
# License: CC0 1.0 Universal

"""Tests for downloader"""

import os
import sys
import errno
import shutil
import unittest
from tempfile import mkdtemp

import mock

try:
    from landsat.downloader import Downloader, RemoteFileDoesntExist, IncorrectSceneId
    from landsat.settings import GOOGLE_STORAGE, S3_LANDSAT
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../landsat')))
    from landsat.downloader import Downloader, RemoteFileDoesntExist, IncorrectSceneId
    from landsat.settings import GOOGLE_STORAGE, S3_LANDSAT


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

    @mock.patch('landsat.downloader.fetch')
    def test_download(self, mock_fetch):
        mock_fetch.return_value = True

        # download one list
        self.d.download([self.scene])
        self.assertTrue(self.d.download([self.scene]))

        # Test if error is raised when passing scene as string instead of list
        self.assertRaises(Exception, self.d.download, self.scene)

        # Test if download works when passing scenes as list
        self.d.download([self.scene, self.scene])
        self.assertTrue(self.d.download([self.scene]))

        # Test when passing band list along with sceneID
        self.d.download([self.scene_s3], bands=[11])

        self.assertTrue(self.d.download([self.scene]))

        # Test whether passing band as string raises an exception
        self.assertRaises(Exception, self.d.download, self.scene, 4)

    @mock.patch('landsat.downloader.Downloader.amazon_s3')
    @mock.patch('landsat.downloader.Downloader.google_storage')
    def test_download_google_amazon(self, fake_google, fake_amazon):
        """ Test whether google or amazon are correctly selected based on input """

        fake_amazon.return_value = True
        fake_google.return_value = False

        # Test if google is used when an image from 2014 is passed even if bands are provided
        self.d.download([self.scene], bands=[432])
        fake_google.assert_called_with(self.scene, self.d.download_dir)

        # Test if amazon is used when an image from 2015 is passed with bands
        self.d.download([self.scene_s3], bands=[432])
        fake_amazon.assert_called_with(self.scene_s3, 'MTL', self.d.download_dir + '/' + self.scene_s3)

    @mock.patch('landsat.downloader.fetch')
    def test_google_storage(self, mock_fetch):
        mock_fetch.return_value = True

        # If the file exist
        self.assertTrue(self.d.google_storage(self.scene, self.temp_folder))

        # If scene id is incorrect
        self.assertRaises(IncorrectSceneId, self.d.google_storage, 'somerandomscene', self.temp_folder)

        # If scene id doesn't exist
        self.assertRaises(RemoteFileDoesntExist, self.d.google_storage, 'LG21360082013227LGN01',
                          self.temp_folder)

    @mock.patch('landsat.downloader.fetch')
    def test_amazon_s3(self, mock_fetch):
        mock_fetch.return_value = True

        scene = self.scene_s3
        self.assertTrue(self.d.amazon_s3(scene, 11, self.temp_folder))

        # If scene id is incorrect
        self.assertRaises(IncorrectSceneId, self.d.amazon_s3, 'somerandomscene', 11, self.temp_folder)

        # If scene id doesn't exist
        self.assertRaises(RemoteFileDoesntExist, self.d.amazon_s3, 'LT81360082013127LGN01', 33, self.temp_folder)

    @mock.patch('landsat.downloader.fetch')
    def test_fetch(self, mock_fetch):
        mock_fetch.return_value = True

        sat = self.d.scene_interpreter(self.scene)
        url = self.d.google_storage_url(sat)

        self.assertTrue(self.d.fetch(url, self.temp_folder, self.scene))

    def test_remote_file_size(self):

        url = self.d.google_storage_url(self.d.scene_interpreter(self.scene))
        size = self.d.get_remote_file_size(url)

        self.assertEqual(self.scene_size, size)

    def test_google_storage_url(self):
        sat = self.d.scene_interpreter(self.scene)

        string = self.d.google_storage_url(sat)
        expect = os.path.join(GOOGLE_STORAGE, 'L8/136/008/LT81360082013127LGN01.tar.bz')
        self.assertEqual(expect, string)

    def test_amazon_s3_url(self):
        sat = self.d.scene_interpreter(self.scene)
        filename = '%s_B11.TIF' % self.scene

        string = self.d.amazon_s3_url(sat, filename)
        expect = os.path.join(S3_LANDSAT, 'L8/136/008/LT81360082013127LGN01/LT81360082013127LGN01_B11.TIF')

        self.assertEqual(expect, string)

    def test_remote_file_exist(self):
        # Test a S3 url that exists
        self.assertTrue(self.d.remote_file_exists(os.path.join(S3_LANDSAT, 'L8/003/017/LC80030172015001L'
                                                  'GN00/LC80030172015001LGN00_B6.TIF')))

        # Test a S3 url that doesn't exist
        self.assertFalse(self.d.remote_file_exists(os.path.join(S3_LANDSAT, 'L8/003/017/LC80030172015001L'
                                                   'GN00/LC80030172015001LGN00_B34.TIF')))

        # Test a Google Storage url that doesn't exist
        self.assertFalse(self.d.remote_file_exists(os.path.join(GOOGLE_STORAGE, 'L8/003/017/LC80030172015001L'
                                                   'GN00/LC80030172015001LGN00_B6.TIF')))

        # Test a Google Storage url that exists
        self.assertTrue(self.d.remote_file_exists(os.path.join(GOOGLE_STORAGE,
                                                  'L8/003/017/LC80030172015001LGN00.tar.bz')))

    def test_scene_interpreter(self):
        # Test with correct input
        scene = 'LC80030172015001LGN00'
        ouput = self.d.scene_interpreter(scene)
        self.assertEqual({'path': '003', 'row': '017', 'sat': 'L8', 'scene': scene}, ouput)

        # Test with incorrect input
        self.assertRaises(Exception, self.d.scene_interpreter, 'LC80030172015001LGN')

if __name__ == '__main__':
    unittest.main()
