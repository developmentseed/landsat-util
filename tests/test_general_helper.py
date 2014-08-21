# USGS Landsat Imagery Util
#
#
# Author: developmentseed
# Contributer: scisco
#
# License: CC0 1.0 Universal

"""Tests for general_helper"""

import os
import sys
import errno
import shutil
import unittest
from tempfile import mkdtemp, mkstemp

try:
    import landsat.general_helper as g
except ImportError:
    sys.path.append(os.path
                      .abspath(os.path
                                 .join(os.path.dirname(__file__),
                                       '../landsat')))
    import general_helper as g


class TestGeneralHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_folder_base = mkdtemp()
        cls.temp_folder_test = cls.temp_folder_base + '/test'
        cls.temp_file = mkstemp(dir=cls.temp_folder_base)

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree(cls.temp_folder_base)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def test_create_paired_list(self):
        # Test correct input (string)
        output = g.create_paired_list('003,003,004,004')
        self.assertEqual([('003', '003'), ('004', '004')], output)

        # Test correct input (list)
        output = g.create_paired_list(['003', '003', '004', '004'])
        self.assertEqual([('003', '003'), ('004', '004')], output)

        # Test incorrect input
        self.assertRaises(ValueError, g.create_paired_list, '003,003,004')
        self.assertRaises(ValueError, g.create_paired_list, '')


    def test_check_create_folder(self):
        new_path = g.check_create_folder(self.temp_folder_test)

        self.assertEqual(new_path, self.temp_folder_test)

    def test_get_file(self):
        f = g.get_file(self.temp_folder_test)

        self.assertEqual('test', f)

    def test_get_filename(self):
        # Easy filename
        f = g.get_filename('%s/filename.html' % self.temp_folder_base)
        self.assertEqual('filename', f)

        # Dificult filename
        f = g.get_filename('%s/filename.test.html' % self.temp_folder_base)
        self.assertEqual('filename.test', f)

    def test_three_digit(self):
        self.assertEqual('009', g.three_digit(9))
        self.assertEqual('010', g.three_digit(10))
        self.assertEqual('100', g.three_digit(100))
        self.assertEqual('string', g.three_digit('string'))

    def test_georgian_day(self):
        self.assertEqual(28, g.georgian_day('01/28/2014'))
        self.assertEqual(79, g.georgian_day('03/20/2014'))
        self.assertEqual(0, g.georgian_day('random text'))
        self.assertEqual(0, g.georgian_day(9876))

    def test_year(self):
        self.assertEqual(2014, g.year('01/28/2014'))
        self.assertEqual(0, g.year('2014'))

    def test_reformat_date(self):
        self.assertEqual('28/01/2014', g.reformat_date('01/28/2014',
                                                       '%d/%m/%Y'))
        self.assertEqual('2014', g.reformat_date('2014', '%d/%m/%Y'))
        self.assertEqual('2014', g.reformat_date('2014', 'juberish'))


if __name__ == '__main__':
    unittest.main()
