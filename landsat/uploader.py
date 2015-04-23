# Boto Uploader
# Landsat Util
# License: CC0 1.0 Universal

# The S3 uploader is a fork of pys3upload (https://github.com/leetreveil/pys3upload)

from __future__ import print_function, division

import os
import sys
import time
import threading
import contextlib
import Queue
from multiprocessing import pool
try:
    import cStringIO
    StringIO = cStringIO
except ImportError:
    import StringIO

from boto.s3.connection import S3Connection
from mixins import VerbosityMixin

STREAM = sys.stderr


class Uploader(VerbosityMixin):

    progress_template = \
        'File Size:%(size)4d MB | Uploaded:%(uploaded)4d MB' + ' ' * 8

    def __init__(self, key=None, secret=None, host=None):
        self.key = key
        self.secret = secret
        self.source_size = 0
        self.conn = S3Connection(key, secret, host=host)

    def run(self, bucket_name, filename, path):

        f = open(path, 'rb')
        self.source_size = os.stat(path).st_size
        total_dict = {}

        def cb(part_no, uploaded, total):

            total_dict[part_no] = uploaded

            params = {
                'uploaded': round(sum(total_dict.values()) / 1048576, 0),
                'size': round(self.source_size / 1048576, 0),
            }

            p = (self.progress_template + '\r') % params

            STREAM.write(p)
            STREAM.flush()

        self.output('Uploading to S3', normal=True, arrow=True)
        upload(bucket_name, self.key, self.secret,
               data_collector(f.readlines()), filename, cb,
               threads=10, replace=True, secure=True, connection=self.conn)

        print('\n')
        self.output('Upload Completed', normal=True, arrow=True)


def data_collector(iterable, def_buf_size=5242880):
    ''' Buffers n bytes of data

        Args:
            iterable: could be a list, generator or string
            def_buf_size: number of bytes to buffer, default is 5mb

        Returns:
            A generator object
    '''
    buf = ''
    for data in iterable:
        buf += data
        if len(buf) >= def_buf_size:
            output = buf[:def_buf_size]
            buf = buf[def_buf_size:]
            yield output
    if len(buf) > 0:
        yield buf


def upload_part(upload_func, progress_cb, part_no, part_data):
    num_retries = 5

    def _upload_part(retries_left=num_retries):
        try:
            with contextlib.closing(StringIO.StringIO(part_data)) as f:
                f.seek(0)
                cb = lambda c, t: progress_cb(part_no, c, t) if progress_cb else None
                upload_func(f, part_no, cb=cb, num_cb=100)
        except Exception, exc:
            retries_left -= 1
            if retries_left > 0:
                return _upload_part(retries_left=retries_left)
            else:
                return threading.ThreadError(repr(threading.current_thread()) + ' ' + repr(exc))
    return _upload_part()


def upload(bucket, aws_access_key, aws_secret_key,
           iterable, key, progress_cb=None,
           threads=5, replace=False, secure=True,
           connection=None):
    ''' Upload data to s3 using the s3 multipart upload API.

        Args:
            bucket: name of s3 bucket
            aws_access_key: aws access key
            aws_secret_key: aws secret key
            iterable: The data to upload. Each 'part' in the list
            will be uploaded in parallel. Each part must be at
            least 5242880 bytes (5mb).
            key: the name of the key to create in the s3 bucket
            progress_cb: will be called with (part_no, uploaded, total)
            each time a progress update is available.
            threads: the number of threads to use while uploading. (Default is 5)
            replace: will replace the key in s3 if set to true. (Default is false)
            secure: use ssl when talking to s3. (Default is true)
            connection: used for testing
    '''

    if not connection:
        from boto.s3.connection import S3Connection as connection
        c = connection(aws_access_key, aws_secret_key, is_secure=secure)
    else:
        c = connection

    b = c.get_bucket(bucket)

    if not replace and b.lookup(key):
        raise Exception('s3 key ' + key + ' already exists')

    multipart_obj = b.initiate_multipart_upload(key)
    err_queue = Queue.Queue()
    lock = threading.Lock()
    upload.counter = 0

    try:
        tpool = pool.ThreadPool(processes=threads)

        def check_errors():
            try:
                exc = err_queue.get(block=False)
            except Queue.Empty:
                pass
            else:
                raise exc

        def waiter():
            while upload.counter >= threads:
                check_errors()
                time.sleep(0.1)

        def cb(err):
            if err:
                err_queue.put(err)
            with lock:
                upload.counter -= 1

        args = [multipart_obj.upload_part_from_file, progress_cb]

        for part_no, part in enumerate(iterable):
            part_no += 1
            tpool.apply_async(upload_part, args + [part_no, part], callback=cb)
            with lock:
                upload.counter += 1
            waiter()

        tpool.close()
        tpool.join()
        # Check for thread errors before completing the upload,
        # sometimes an error can be left unchecked until we
        # get to this point.
        check_errors()
        multipart_obj.complete_upload()
    except:
        multipart_obj.cancel_upload()
        tpool.terminate()
        raise
