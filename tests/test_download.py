# Landsat Util
# License: CC0 1.0 Universal

"""Tests for downloader"""

import os
import errno
import shutil
import unittest
from tempfile import mkdtemp

import mock

from landsat.downloader import Downloader, RemoteFileDoesntExist, IncorrectSceneId
from landsat.settings import GOOGLE_STORAGE, S3_LANDSAT


class TestDownloader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_folder = mkdtemp()
        cls.d = Downloader(download_dir=cls.temp_folder)
        cls.scene = 'LT81360082013127LGN01'
        cls.scene_2 = 'LC82050312014229LGN00'
        cls.scene_s3 = 'LC80010092015051LGN00'
        cls.scene_s3_2 = 'LC82050312015136LGN00'
        cls.scene_size = 59239149

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

        # download one scene
        self.d.download([self.scene])
        paths = self.d.download([self.scene])
        self.assertTrue(isinstance(paths, list))
        self.assertEqual([self.temp_folder + '/' + self.scene + '.tar.bz'],
                         paths)

        # download multiple scenes
        paths = self.d.download([self.scene, self.scene_2])
        test_paths = [self.temp_folder + '/' + self.scene + '.tar.bz',
                      self.temp_folder + '/' + self.scene_2 + '.tar.bz']
        self.assertTrue(isinstance(paths, list))
        self.assertEqual(test_paths, paths)

        # Test if error is raised when passing scene as string instead of list
        self.assertRaises(Exception, self.d.download, self.scene)

        # Test when passing band list along with sceneID
        paths = self.d.download([self.scene_s3, self.scene_s3_2], bands=[11])
        test_paths = [self.temp_folder + '/' + self.scene_s3,
                      self.temp_folder + '/' + self.scene_s3_2]
        self.assertEqual(test_paths, paths)

        # When passing scene as string, google storage download should be triggered
        paths = self.d.download([self.scene], bands=4)
        test_paths = [self.temp_folder + '/' + self.scene + '.tar.bz']
        self.assertEqual(test_paths, paths)

    @mock.patch('landsat.downloader.Downloader.google_storage')
    def test_download_google_when_amazon_is_unavailable(self, fake_google):
        """ Test whether google or amazon are correctly selected based on input """

        fake_google.return_value = False

        # Test if google is used when an image from 2014 is passed even if bands are provided
        self.d.download([self.scene], bands=[432])
        fake_google.assert_called_with(self.scene, self.d.download_dir)

    @mock.patch('landsat.downloader.fetch')
    def test_download_amazon_when_available(self, mock_fetch):
        """ Test whether google or amazon are correctly selected based on input """

        mock_fetch.return_value = True

        # Test if amazon is used when an image from 2015 is passed with bands
        paths = self.d.download([self.scene_s3], bands=[4, 3, 2])
        test_paths = [self.temp_folder + '/' + self.scene_s3]
        self.assertEqual(test_paths, paths)

    @mock.patch('landsat.downloader.fetch')
    def test_fetch(self, mock_fetch):
        mock_fetch.return_value = True

        sat = self.d.scene_interpreter(self.scene)
        url = self.d.google_storage_url(sat)

        self.assertTrue(self.d.fetch(url, self.temp_folder))

    def test_remote_file_size(self):

        url = self.d.google_storage_url(self.d.scene_interpreter(self.scene))
        size = self.d.get_remote_file_size(url)

        self.assertAlmostEqual(self.scene_size, size)

    def test_google_storage_url(self):
        sat = self.d.scene_interpreter(self.scene)

        string = self.d.google_storage_url(sat)
        expect = os.path.join(GOOGLE_STORAGE, 'L8/136/008/LT81360082013127LGN01.tar.bz')
        self.assertEqual(expect, string)

    def test_amazon_s3_url(self):
        sat = self.d.scene_interpreter(self.scene)
        string = self.d.amazon_s3_url(sat, 11)
        expect = os.path.join(S3_LANDSAT, 'L8/136/008/LT81360082013127LGN01/LT81360082013127LGN01_B11.TIF')

        self.assertEqual(expect, string)

    def test_remote_file_exist(self):
        # Exists and should return None

        self.assertIsNone(self.d.remote_file_exists(os.path.join(S3_LANDSAT, 'L8/003/017/LC80030172015001L'
                                                    'GN00/LC80030172015001LGN00_B6.TIF')))

        # Doesn't exist and should raise errror
        with self.assertRaises(RemoteFileDoesntExist):
            self.d.remote_file_exists(
                os.path.join(
                    S3_LANDSAT,
                    'L8/003/017/LC80030172015001LGN00/LC80030172015001LGN00_B34.TIF'
                )
            )

        # Doesn't exist and should raise errror
        with self.assertRaises(RemoteFileDoesntExist):
            self.d.remote_file_exists(
                os.path.join(
                    GOOGLE_STORAGE,
                    'L8/003/017/LC80030172015001LGN00/LC80030172015001LGN00_B6.TIF'
                )
            )

        # Exist and shouldn't raise error
        self.assertIsNone(self.d.remote_file_exists(os.path.join(GOOGLE_STORAGE,
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
