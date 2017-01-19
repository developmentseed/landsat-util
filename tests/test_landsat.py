# Landsat Util
# License: CC0 1.0 Universal

"""Tests for landsat"""

import json
import unittest
import subprocess
import errno
import shutil
from os.path import join

from jsonschema import validate
import mock

import landsat.landsat as landsat
from tests import geojson_schema


class TestLandsat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parser = landsat.args_options()
        cls.mock_path = 'path/to/folder'

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree('path')
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def test_incorrect_date(self):
        """ Test search with incorrect date input """

        args = ['search', '--start', 'berlin', '--end', 'january 10 2014']

        self.assertEquals(landsat.main(self.parser.parse_args(args)),
                          ['Your date format is incorrect. Please try again!', 1])

    def test_too_many_results(self):
        """ Test when search return too many results """

        args = ['search', '--cloud', '100', '-p', '205,022,206,022,204,022']

        self.assertEquals(landsat.main(self.parser.parse_args(args)),
                          ['Over 100 results. Please narrow your search', 1])

    def test_search_pr_correct(self):
        """Test Path Row search with correct input"""
        args = ['search', '--start', 'january 1 2013', '--end',
                'january 10 2014', '-p', '008,008']

        self.assertEquals(landsat.main(self.parser.parse_args(args)),
                          ['Search completed!'])

    def test_search_lat_lon(self):
        """Test Latitude Longitude search with correct input"""
        args = ['search', '--start', 'may 01 2013', '--end', 'may 08 2013',
                '--lat', '38.9107203', '--lon', '-77.0290116']

        self.assertEquals(landsat.main(self.parser.parse_args(args)),
                          ['Search completed!'])

    def test_search_pr_wrong_input(self):
        """Test Path Row search with incorrect input"""
        args = ['search', '-p', 'what?']

        self.assertEquals(landsat.main(self.parser.parse_args(args)), None)

    def test_search_json_output(self):
        """Test json output in search"""
        args = ['search', '--latest', '10', '--json']

        output = landsat.main(self.parser.parse_args(args))
        j = json.loads(output)

        self.assertEquals(type(j), dict)

    def test_search_geojson_output(self):
        """Test json output in search"""
        args = ['search', '--latest', '10', '--geojson']

        output = landsat.main(self.parser.parse_args(args))
        j = json.loads(output)

        self.assertIsNone(validate(j, geojson_schema))
        self.assertEquals(type(j), dict)

    @mock.patch('landsat.landsat.Downloader')
    def test_download_correct(self, mock_downloader):
        """Test download command with correct input"""
        mock_downloader.download.return_value = True

        args = ['download', 'LC80010092015051LGN00', '-b', '11,', '-d', self.mock_path]
        output = landsat.main(self.parser.parse_args(args))
        mock_downloader.assert_called_with(download_dir=self.mock_path, usgs_pass=None, usgs_user=None)
        mock_downloader.return_value.download.assert_called_with(['LC80010092015051LGN00'], [11])
        self.assertEquals(output, ['Download Completed', 0])

    @mock.patch('landsat.landsat.Downloader')
    def test_download_correct_zip(self, mock_downloader):
        """Download command should download zip if no bands are given"""
        mock_downloader.download.return_value = True

        args = ['download', 'LC80010092015051LGN00', '-d', self.mock_path]
        output = landsat.main(self.parser.parse_args(args))
        mock_downloader.assert_called_with(download_dir=self.mock_path, usgs_pass=None, usgs_user=None)
        mock_downloader.return_value.download.assert_called_with(['LC80010092015051LGN00'], None)
        self.assertEquals(output, ['Download Completed', 0])

    @mock.patch('landsat.landsat.process_image')
    @mock.patch('landsat.landsat.Downloader.download')
    def test_download_no_bands_with_process(self, mock_downloader, mock_process):
        """Download command should not download zip if no bands are given but process flag is used"""
        mock_downloader.return_value = {'LC80010092015051LGN00': 'aws'}
        mock_process.return_value = 'image.TIF'

        args = ['download', 'LC80010092015051LGN00', '-p', '-d', self.mock_path]
        output = landsat.main(self.parser.parse_args(args))
        mock_downloader.assert_called_with(['LC80010092015051LGN00'], [4, 3, 2])
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

    def test_download_incorrect(self):
        """Test download command with incorrect input"""
        args = ['download', 'LT813600']

        self.assertEquals(landsat.main(self.parser.parse_args(args)),
                          ['The SceneID provided was incorrect', 1])

    @mock.patch('landsat.landsat.process_image')
    @mock.patch('landsat.downloader.fetch')
    def test_download_process_continuous(self, fetch, mock_process):
        """Test download and process commands together"""
        fetch.return_value = True
        mock_process.return_value = 'image.TIF'

        args = ['download', 'LC80010092015051LGN00', 'LC80470222014354LGN00', '-b', '432', '-d', self.mock_path, '-p']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80470222014354LGN00', '432',
                                        False, False, False, False, False, bounds=None)
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

        # Call with force unzip flag
        args = ['download', 'LC80010092015051LGN00', 'LC80470222014354LGN00', '-b', '432', '-d',
                self.mock_path, '-p', '--force-unzip']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80470222014354LGN00', '432', False, False, False,
                                        True, False, bounds=None)
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

        # Call with pansharpen
        args = ['download', 'LC80010092015051LGN00', 'LC80470222014354LGN00', '-b', '432', '-d',
                self.mock_path, '-p', '--pansharpen']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80470222014354LGN00', '432', False, True, False,
                                        False, False, bounds=None)
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

        # Call with pansharpen and clipping
        args = ['download', 'LC80010092015051LGN00', 'LC80470222014354LGN00', '-b', '432', '-d',
                self.mock_path, '-p', '--pansharpen', '--clip', '"-180,-180,0,0"']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80470222014354LGN00', '432', False, True, False,
                                        False, False, bounds=[-180.0, -180.0, 0.0, 0.0])
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

        # Call with ndvi
        args = ['download', 'LC80010092015051LGN00', 'LC80470222014354LGN00', '-b', '432', '-d',
                self.mock_path, '-p', '--ndvi']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80470222014354LGN00', '432', False, False, True,
                                        False, False, bounds=None)
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

        # Call with ndvigrey
        args = ['download', 'LC80010092015051LGN00', 'LC80470222014354LGN00', '-b', '432', '-d',
                self.mock_path, '-p', '--ndvigrey']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80470222014354LGN00', '432', False, False, False,
                                        False, True, bounds=None)
        self.assertEquals(output, ["The output is stored at image.TIF", 0])

    @mock.patch('landsat.landsat.Uploader')
    @mock.patch('landsat.landsat.process_image')
    @mock.patch('landsat.downloader.fetch')
    def test_download_process_continuous_with_upload(self, fetch, mock_process, mock_upload):
        """Test download and process commands together"""
        fetch.return_value = True
        mock_process.return_value = 'image.TIF'
        mock_upload.run.return_value = True

        args = ['download', 'LC80010092015051LGN00', '-b', '432', '-d', self.mock_path, '-p',
                '-u', '--key', 'somekey', '--secret', 'somesecret', '--bucket', 'mybucket', '--region', 'this']
        output = landsat.main(self.parser.parse_args(args))
        # mock_downloader.assert_called_with(['LC80010092015051LGN00'], [4, 3, 2])
        mock_process.assert_called_with('path/to/folder/LC80010092015051LGN00', '432', False, False, False,
                                        False, False, bounds=None)
        mock_upload.assert_called_with('somekey', 'somesecret', 'this')
        mock_upload.return_value.run.assert_called_with('mybucket', 'image.TIF', 'image.TIF')
        self.assertEquals(output, ['The output is stored at image.TIF', 0])

    @mock.patch('landsat.landsat.process_image')
    @mock.patch('landsat.downloader.fetch')
    def test_download_process_continuous_with_wrong_args(self, fetch, mock_process):
        """Test download and process commands together"""
        fetch.return_value = True
        mock_process.return_value = 'image.TIF'

        args = ['download', 'LC80010092015051LGN00', '-b', '432', '-d', self.mock_path, '-p',
                '-u', '--region', 'whatever']
        output = landsat.main(self.parser.parse_args(args))
        mock_process.assert_called_with('path/to/folder/LC80010092015051LGN00', '432', False, False, False,
                                        False, False, bounds=None)
        self.assertEquals(output, ['Could not authenticate with AWS', 1])

    @mock.patch('landsat.landsat.process_image')
    def test_process_correct(self, mock_process):
        """Test process command with correct input"""
        mock_process.return_value = 'image.TIF'

        args = ['process', 'path/to/folder/LC80010092015051LGN00']
        output = landsat.main(self.parser.parse_args(args))

        mock_process.assert_called_with('path/to/folder/LC80010092015051LGN00', '432',
                                        False, False, False, False, False, None)
        self.assertEquals(output, ["The output is stored at image.TIF"])

    @mock.patch('landsat.landsat.process_image')
    def test_process_correct_with_clipping(self, mock_process):
        """Test process command with correct input"""
        mock_process.return_value = 'image.TIF'

        args = ['process', 'path/to/folder/LC80010092015051LGN00', '--clip', '"-180,-180,0,0"']
        output = landsat.main(self.parser.parse_args(args))

        mock_process.assert_called_with('path/to/folder/LC80010092015051LGN00', '432',
                                        False, False, False, False, False, [-180.0, -180.0, 0.0, 0.0])
        self.assertEquals(output, ["The output is stored at image.TIF"])

    @mock.patch('landsat.landsat.process_image')
    def test_process_correct_pansharpen(self, mock_process):
        """Test process command with correct input and pansharpening"""
        mock_process.return_value = 'image.TIF'

        args = ['process', '--pansharpen', 'path/to/folder/LC80010092015051LGN00']
        output = landsat.main(self.parser.parse_args(args))

        mock_process.assert_called_with('path/to/folder/LC80010092015051LGN00', '432', False, True, False, False,
                                        False, None)
        self.assertEquals(output, ["The output is stored at image.TIF"])

    @mock.patch('landsat.landsat.process_image')
    def test_process_correct_ndvi(self, mock_process):
        """Test process command with correct input and ndvi"""
        mock_process.return_value = 'image.TIF'

        args = ['process', '--ndvi', 'path/to/folder/LC80010092015051LGN00']
        output = landsat.main(self.parser.parse_args(args))

        mock_process.assert_called_with('path/to/folder/LC80010092015051LGN00', '432', False, False, True, False,
                                        False, None)
        self.assertEquals(output, ["The output is stored at image.TIF"])

    def test_process_incorrect(self):
        """Test process command with incorrect input"""
        args = ['process', 'whatever']

        try:
            landsat.main(self.parser.parse_args(args))
        except SystemExit as e:
            self.assertEqual(e.code, 1)

    def check_command_line(self):
        """ Check if the commandline performs correctly """

        self.assertEqual(subprocess.call(['python', join(self.base_dir, '../landsat.py'), '-h']), 0)


if __name__ == '__main__':
    unittest.main()
