# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco, KAPPS-, kamicut
#
# License: CC0 1.0 Universal

"""Tests for search_helper"""

import os
import sys
import unittest

try:
    from landsat.search_helper import Search
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../landsat')))
    from search_helper import Search


class TestSearchHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.s = Search()

    def test_search(self):
        # TEST A REGULAR SEARCH WITH KNOWN RESULT
        row_paths = '003,003'
        start_date = '2014-01-01'
        end_date = '2014-06-01'
        cloud_min = 0
        cloud_max = 100
        limit = 10

        result = self.s.search(row_paths=row_paths,
                               start_date=start_date,
                               end_date=end_date)

        self.assertEqual(1, result['total'])

        row_path_list = ['003,003,004',
                         '045503345']

        # TEST VARIOUS FORMATS
        for i in range(len(row_path_list)):
            row_path_list[i]

            result = self.s.search(row_paths=row_paths,
                                   start_date=start_date,
                                   end_date=end_date,
                                   cloud_min=cloud_min,
                                   cloud_max=cloud_max,
                                   limit=limit)

            self.assertIsInstance(result, dict)

    def test_query_builder(self):

        q = [{'rp': '003,003',
              'start': '2014-01-01',
              'end': '2014-06-01',
              'min': 0,
              'max': 100
              },
             {'rp': '003,003',
              'start': '01',
              'end': '2014',
              'min': '',
              'max': ''
              }]

        for i in range(len(q)):
            output = self.s._query_builder(row_paths=q[i]['rp'],
                                           start_date=q[i]['start'],
                                           end_date=q[i]['end'],
                                           cloud_min=q[i]['min'],
                                           cloud_max=q[i]['max'])
            self.assertIsInstance(output, str)

    def test_row_path_builder(self):
        self.assertEqual('row:003+AND+path:003', self.s
                                                     ._row_path_builder('003',
                                                                        '003'))

    def test_date_range_builder(self):
        self.assertEqual('acquisitionDate:[2013+TO+2014]',
                         self.s._date_range_builder('2013', '2014'))

    def test_cloud_cover_prct_range_builder(self):
        self.assertEqual('cloudCoverFull:[1+TO+2]',
                         self.s._cloud_cover_prct_range_builder('1', '2'))

if __name__ == '__main__':
    unittest.main()
