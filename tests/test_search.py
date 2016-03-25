# Landsat Util
# License: CC0 1.0 Universal

"""Tests for search"""

import unittest

from jsonschema import validate

from landsat.search import Search
from tests import geojson_schema


class TestSearchHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.s = Search()

    def test_search(self):
        # TEST A REGULAR SEARCH WITH KNOWN RESULT for paths and rows
        paths_rows = '003,003'
        start_date = '2014-01-01'
        end_date = '2014-06-01'

        result = self.s.search(paths_rows=paths_rows, start_date=start_date, end_date=end_date)
        self.assertEqual('2014-05-22', result['results'][0]['date'])

        # TEST A REGULAR SEARCH WITH KNOWN RESULT for lat and lon
        lat = 38.9107203
        lon = -77.0290116
        start_date = '2015-02-01'
        end_date = '2015-02-20'

        result = self.s.search(lat=lat, lon=lon, start_date=start_date, end_date=end_date)
        self.assertEqual('2015-02-06', result['results'][0]['date'])

    def test_search_zero_lon(self):
        # Make sure that zero coordinates are handled correctly
        paths_rows = '003,003'
        lon = 0.0
        lat = 52.0
        start_date = '2016-01-01'
        end_date = '2016-01-10'

        result = self.s.search(start_date=start_date, end_date=end_date,
                               lon=0.0, lat=52.0)
        self.assertEqual('2016-01-06', result['results'][0]['date'])

    def test_search_with_geojson(self):

        # TEST A REGULAR SEARCH WITH KNOWN RESULT for paths and rows
        paths_rows = '003,003'
        start_date = '2014-01-01'
        end_date = '2014-06-01'

        result = self.s.search(paths_rows=paths_rows, start_date=start_date, end_date=end_date, geojson=True)
        self.assertIsNone(validate(result, geojson_schema))
        self.assertEqual('2014-05-22', result['features'][0]['properties']['date'])

    def test_query_builder(self):
        # test wiht no input
        string = self.s.query_builder()
        self.assertEqual('', string)

        # just with rows and paths
        string = self.s.query_builder(paths_rows='003,004')
        self.assertEqual('(path:003+AND+row:004)', string)

        # multiple rows and paths
        string = self.s.query_builder(paths_rows='003,004,010,001')
        self.assertEqual('(path:003+AND+row:004)+OR+(path:010+AND+row:001)', string)

        # incomplete rows and paths
        self.assertRaises(ValueError, self.s.query_builder, paths_rows='003,004,010')

        # full example
        expected_string = ('acquisitionDate:[2014-01-01+TO+2014-11-12]+AND+cloudCoverFull:[10+TO+28]+AND+upperLeftCo'
                           'rnerLatitude:[23+TO+1000]+AND+lowerRightCornerLatitude:[-1000+TO+23]+AND+lowerLeftCorner'
                           'Longitude:[-1000+TO+21]+AND+upperRightCornerLongitude:[21+TO+1000]+AND+((path:003+AND+ro'
                           'w:004))')
        string = self.s.query_builder(paths_rows='003,004', lat=23, lon=21, start_date='2014-01-01',
                                      end_date='2014-11-12', cloud_min=10, cloud_max=28)
        self.assertEqual(expected_string, string)

    def test_lat_lon_builder(self):
        expected_string = ('upperLeftCornerLatitude:[12.3344+TO+1000]+AND+lowerRightCornerLatitude:[-1000+TO+12.3344]'
                           '+AND+lowerLeftCornerLongitude:[-1000+TO+11.0032]+AND+upperRightCornerLongitude:[11.0032+T'
                           'O+1000]')

        # Test with floats
        string = self.s.lat_lon_builder(12.3344, 11.0032)
        self.assertEqual(expected_string, string)

        # Test with strings
        string = self.s.lat_lon_builder('12.3344', '11.0032')
        self.assertEqual(expected_string, string)

    def test_cloud_cover_prct_range_builder(self):
        # no input
        string = self.s.cloud_cover_prct_range_builder()
        self.assertEqual('cloudCoverFull:[0+TO+100]', string)

        # just min
        string = self.s.cloud_cover_prct_range_builder(3)
        self.assertEqual('cloudCoverFull:[3+TO+100]', string)

        # just max
        string = self.s.cloud_cover_prct_range_builder(max=30)
        self.assertEqual('cloudCoverFull:[0+TO+30]', string)

        # both inputs
        string = self.s.cloud_cover_prct_range_builder(7, 10)
        self.assertEqual('cloudCoverFull:[7+TO+10]', string)

    def test_date_range_builder(self):
        string = self.s.date_range_builder('2014-01-01', '2015-01-01')
        self.assertEqual('acquisitionDate:[2014-01-01+TO+2015-01-01]', string)

    def test_row_path_builder(self):
        string = self.s.row_path_builder('003', '004')
        self.assertEqual('path:003+AND+row:004', string)


if __name__ == '__main__':
    unittest.main()
