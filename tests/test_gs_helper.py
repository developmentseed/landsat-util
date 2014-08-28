# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

"""Tests for gs_helper"""

import os
import sys
import errno
import shutil
import unittest
from tempfile import mkdtemp, mkstemp

try:
    from landsat.gs_helper import GsHelper
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../landsat')))
    from gs_helper import GsHelper


class TestGsHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.g = GsHelper()
        cls.temp_folder = mkdtemp()
        cls.g.download_dir = cls.temp_folder + '/download'
        cls.g.zip_dir = cls.g.download_dir + '/zip'
        cls.g.unzip_dir = cls.g.download_dir + '/unzip'
        cls.g.scene_file = cls.g.download_dir + '/scene_list'

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.temp_folder)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def test_init(self):
        self.assertIsInstance(self.g, GsHelper)

    # @unittest.skip("demonstrating skipping")
    def test_search(self):
        # test wrong query
        self.assertRaises(SystemExit, self.g.search, '334555')

        # test a search with known result
        query = '003,003'
        start = '01/01/2014'
        end = '01/06/2014'

        self.assertEqual(1, len(self.g.search(query, start, end)))

        # test a search with unconvential date range

        query = '003,003'
        start = 'jan 1 2014'
        end = 'june 1 2014'

        self.assertEqual(1, len(self.g.search(query, start, end)))

    # @unittest.skip("demonstrating skipping")
    def test_signle_download(self):
        # Downloading this image: LT81360082013127LGN01.tar.bz since the size
        # is very small: 56.46MB

        self.assertTrue(self.g.single_download('008',
                                               '136',
                                               'LT81360082013127LGN01'))

    # @unittest.skip("demonstrating skipping")
    def test_batch_download(self):
        image_list = ['gs://earthengine-public/landsat/L8/136/008/'
                      'LT81360082013127LGN01.tar.bz',
                      'gs://earthengine-public/landsat/L8/136/008/'
                      'LT81360082013127LGN01.tar.bz']

        self.assertTrue(self.g.batch_download(image_list))

    def test_unzip(self):
        self.assertTrue(self.g.unzip())

if __name__ == '__main__':
    unittest.main()
