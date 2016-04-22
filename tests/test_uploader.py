# Landsat Util
# License: CC0 1.0 Universal

# Some of the tests are from pys3upload (https://github.com/leetreveil/pys3upload)

"""Tests for uploader"""

import os
import sys
import unittest
import threading

import mock

from landsat.uploader import Uploader, upload, upload_part, data_collector
from .mocks import S3Connection, state


class TestUploader(unittest.TestCase):

    @mock.patch('landsat.uploader.S3Connection', S3Connection)
    def test_upload_to_s3(self):
        state['mock_boto_s3_multipart_upload_data'] = []
        base_dir = os.path.abspath(os.path.dirname(__file__))
        landsat_image = os.path.join(base_dir, 'samples/mock_upload')
        f = open(landsat_image, 'rb').readlines()

        u = Uploader('some_key', 'some_secret')
        u.run('some bucket', 'mock_upload', landsat_image)

        self.assertEqual(state['mock_boto_s3_multipart_upload_data'], f)


class upload_tests(unittest.TestCase):

    def test_should_be_able_to_upload_data(self):
        input = [b'12', b'345']
        state['mock_boto_s3_multipart_upload_data'] = []
        conn = S3Connection('some_key', 'some_secret', True)
        upload('test_bucket', 'some_key', 'some_secret', input, 'some_key', connection=conn)
        self.assertEqual(state['mock_boto_s3_multipart_upload_data'], [b'12', b'345'])


class upload_part_tests(unittest.TestCase):

    def test_should_return_error_when_upload_func_raises_error(self):
        def upload_func(*args, **kwargs):
            raise Exception()

        with self.assertRaises(threading.ThreadError):
            raise upload_part(upload_func, '_', '_', '_')

    def test_should_retry_upload_five_times(self):
        counter = [0]

        def upload_func(*args, **kwargs):
            counter[0] += 1
            raise Exception()

        upload_part(upload_func, b'_', b'_', b'_')
        self.assertEqual(counter[0], 5)


class doc_collector_tests(unittest.TestCase):

    def test_should_be_able_to_read_every_byte_of_data(self):
        input = [b'12345']
        result = list(data_collector(input, def_buf_size=3))
        self.assertEqual(result, [b'123', b'45'])

    def test_should_be_able_to_read_single_yield(self):
        input = [b'123']
        result = list(data_collector(input, def_buf_size=3))
        self.assertEqual(result, [b'123'])

    def test_should_be_able_to_yield_data_less_than_buffer_size(self):
        input = [b'123']
        result = list(data_collector(input, def_buf_size=6))
        self.assertEqual(result, [b'123'])

    def test_a_single_item_should_still_be_buffered_even_if_it_is_above_the_buffer_size(self):
        input = [b'123456']
        result = list(data_collector(input, def_buf_size=3))
        self.assertEqual(result, [b'123', b'456'])

    def test_should_return_rest_of_data_on_last_iteration(self):
        input = [b'1234', b'56']
        result = list(data_collector(input, def_buf_size=3))
        self.assertEqual(result, [b'123', b'456'])

if __name__ == '__main__':
    unittest.main()
