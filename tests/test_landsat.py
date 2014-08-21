# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

"""Tests for landsat"""

import os
import sys
import unittest

try:
    import landsat.landsat as landsat
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../landsat')))
    import landsat

class MockOptions(object):
    """ Create Mock commandline options """

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class TestLandsat(unittest.TestCase):
    dictionary = {
        'rows_paths': None,
        'start': None,
        'end': None,
        'cloud': None,
        'limit': 100,
        'direct': None,
        'shapefile': None,
        'country': None,
        'umeta': None
    }

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.abspath(os.path.dirname(__file__))
        cls.shapefile = cls.base_dir + '/samples/test_shapefile.shp'

    # @unittest.skip('Takes too much time')
    def test_search_rows_paths_without_date_cloud(self):
        self.dictionary['rows_paths'] = '136,008'
        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)

    # @unittest.skip('Takes too much time')
    def test_search_rows_paths_w_date_no_cloud(self):
        self.dictionary['rows_paths'] = '008,136'
        self.dictionary['start'] = 'May 1 2013'
        self.dictionary['end'] = 'May 15 2013'

        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)

    # @unittest.skip('Takes too much time')
    def test_search_rows_paths_w_date_cloud(self):
        self.dictionary['rows_paths'] = '008,136'
        self.dictionary['start'] = 'May 1 2013'
        self.dictionary['end'] = 'May 15 2013'
        self.dictionary['cloud'] = 100

        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)

    # @unittest.skip('Takes too much time')
    def test_direct_search(self):
        self.dictionary['direct'] = True
        self.dictionary['rows_paths'] = '136,008'
        self.dictionary['start'] = 'May 1 2013'
        self.dictionary['end'] = 'May 15 2013'

        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)

    # @unittest.skip('Takes too much time')
    def test_shapefile(self):
        self.dictionary['shapefile'] = self.shapefile

        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)

    # @unittest.skip('Takes too much time')
    def test_country(self):
        self.dictionary['country'] = 'Maldives'

        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)

    def test_metada(self):
        self.dictionary['umeta'] = True

        m = MockOptions(**self.dictionary)

        self.assertRaises(SystemExit, landsat.main, m)




if __name__ == '__main__':
    unittest.main()

