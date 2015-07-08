# Landsat Util
# License: CC0 1.0 Universal

"""Tests for utils"""

from os.path import join
import errno
import shutil
import unittest
from tempfile import mkdtemp, mkstemp

from landsat import utils


class TestUtils(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_folder_base = mkdtemp()
        cls.temp_folder_test = join(cls.temp_folder_base, 'test')
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
        output = utils.create_paired_list('003,003,004,004')
        self.assertEqual([['003', '003'], ['004', '004']], output)

        # Test correct input (list)
        output = utils.create_paired_list(['003', '003', '004', '004'])
        self.assertEqual([['003', '003'], ['004', '004']], output)

        # Test incorrect input
        self.assertRaises(ValueError, utils.create_paired_list, '003,003,004')
        self.assertRaises(ValueError, utils.create_paired_list, '')

    def test_check_create_folder(self):
        new_path = utils.check_create_folder(self.temp_folder_test)

        self.assertEqual(new_path, self.temp_folder_test)

    def test_get_file(self):
        f = utils.get_file(self.temp_folder_test)

        self.assertEqual('test', f)

    def test_get_filename(self):
        # Easy filename
        f = utils.get_filename('%s/filename.html' % self.temp_folder_base)
        self.assertEqual('filename', f)

        # Dificult filename
        f = utils.get_filename('%s/filename.test.html' % self.temp_folder_base)
        self.assertEqual('filename.test', f)

    def test_three_digit(self):
        self.assertEqual('009', utils.three_digit(9))
        self.assertEqual('010', utils.three_digit(10))
        self.assertEqual('100', utils.three_digit(100))
        self.assertEqual('string', utils.three_digit('string'))

    def test_georgian_day(self):
        self.assertEqual(28, utils.georgian_day('01/28/2014'))
        self.assertEqual(79, utils.georgian_day('03/20/2014'))
        self.assertEqual(0, utils.georgian_day('random text'))
        self.assertEqual(0, utils.georgian_day(9876))

    def test_year(self):
        self.assertEqual(2014, utils.year('01/28/2014'))
        self.assertEqual(0, utils.year('2014'))

    def test_reformat_date(self):

        self.assertEqual('2014-02-03', utils.reformat_date('02/03/2014'))
        self.assertEqual('2014-03-02', utils.reformat_date('02/03/2014', '%Y-%d-%m'))
        self.assertEqual('2014', utils.reformat_date('2014', '%d/%m/%Y'))
        self.assertEqual('2014', utils.reformat_date('2014', 'juberish'))
        self.assertRaises(TypeError, utils.reformat_date('date'))

    def test_convert_to_integer_list(self):
        # correct input
        r = utils.convert_to_integer_list('1,2,3')
        self.assertEqual([1, 2, 3], r)

        # try other cobinations
        r = utils.convert_to_integer_list('1, 2, 3')
        self.assertEqual([1, 2, 3], r)

        r = utils.convert_to_integer_list('1s,2df,3d/')
        self.assertEqual([1, 2, 3], r)

        r = utils.convert_to_integer_list([1, 3, 4])
        self.assertEqual([1, 3, 4], r)

        r = utils.convert_to_integer_list('1,11,10')
        self.assertEqual([1, 11, 10], r)

        r = utils.convert_to_integer_list('1,11,10,QA')
        self.assertEqual([1, 11, 10, 'QA'], r)


if __name__ == '__main__':
    unittest.main()
