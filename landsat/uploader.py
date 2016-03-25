# Boto Uploader
# Landsat Util
# License: CC0 1.0 Universal

# The S3 uploader is a fork of pys3upload (https://github.com/leetreveil/pys3upload)

from __future__ import print_function, division, absolute_import

import os
import sys
import time
import threading
import contextlib

try:
    import queue
except:
    import Queue as queue

from multiprocessing import pool

try:
    from io import BytesIO as StringIO
except ImportError:
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO

from boto.s3.connection import S3Connection

from .mixins import VerbosityMixin

STREAM = sys.stderr


class Uploader(VerbosityMixin):

    """
    The Uploader class.

    To initiate the following parameters must be passed:

    :param key:
        AWS access key id (optional)
    :type key:
        String
    :param secret:
        AWS access secret key (optional)
    :type secret:
        String
    :param host:
        AWS host, e.g. s3.amazonaws.com (optional)
    :type host:
        String
    """

    progress_template = \
        'File Size:%(size)4d MB | Uploaded:%(uploaded)4d MB' + ' ' * 8

    def __init__(self, key=None, secret=None, host=None):
        self.key = key
        self.secret = secret
        self.source_size = 0
        self.conn = S3Connection(key, secret, host=host)

    def run(self, bucket_name, filename, path):
        """
        Initiate the upload.

        :param bucket_name:
            Name of the S3 bucket
        :type bucket_name:
            String
        :param filename:
            The filname
        :type filename:
            String
        :param path:
            The path to the file that needs to be uploaded
        :type path:
            String

        :returns:
            void
        """

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
               data_collector(iter(f)), filename, cb,
               threads=10, replace=True, secure=True, connection=self.conn)

        print('\n')
        self.output('Upload Completed', normal=True, arrow=True)


def data_collector(iterable, def_buf_size=5242880):
    """ Buffers n bytes of data.

    :param iterable:
        Could be a list, generator or string
    :type iterable:
        List, generator, String

    :returns:
        A generator object
    """
    buf = b''
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
            with contextlib.closing(StringIO(part_data)) as f:
                f.seek(0)
                cb = lambda c, t: progress_cb(part_no, c, t) if progress_cb else None
                upload_func(f, part_no, cb=cb, num_cb=100)
        except Exception as exc:
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
    """ Upload data to s3 using the s3 multipart upload API.

    :param bucket:
        Name of the S3 bucket
    :type bucket:
        String
    :param aws_access_key:
        AWS access key id (optional)
    :type aws_access_key:
        String
    :param aws_secret_key:
        AWS access secret key (optional)
    :type aws_secret_key:
        String
    :param iterable:
        The data to upload. Each 'part' in the list. will be uploaded in parallel. Each part must be at
        least 5242880 bytes (5mb).
    :type iterable:
        An iterable object
    :param key:
        The name of the key (filename) to create in the s3 bucket
    :type key:
        String
    :param progress_cb:
        Progress callback, will be called with (part_no, uploaded, total) each time a progress update
        is available. (optional)
    :type progress_cb:
        function
    :param threads:
        the number of threads to use while uploading. (Default is 5)
    :type threads:
        int
    :param replace:
        will replace the key (filename) on S3 if set to true. (Default is false)
    :type replace:
        boolean
    :param secure:
        Use ssl when talking to s3. (Default is true)
    :type secure:
        boolean
    :param connection:
        Used for testing (optional)
    :type connection:
        S3 connection class

    :returns:
        void
    """

    if not connection:
        from boto.s3.connection import S3Connection as connection
        c = connection(aws_access_key, aws_secret_key, is_secure=secure)
    else:
        c = connection

    b = c.get_bucket(bucket)

    if not replace and b.lookup(key):
        raise Exception('s3 key ' + key + ' already exists')

    multipart_obj = b.initiate_multipart_upload(key)
    err_queue = queue.Queue()
    lock = threading.Lock()
    upload.counter = 0

    try:
        tpool = pool.ThreadPool(processes=threads)

        def check_errors():
            try:
                exc = err_queue.get(block=False)
            except queue.Empty:
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
