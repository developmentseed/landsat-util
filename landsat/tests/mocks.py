state = {}


class MockBotoS3MultipartUpload():
    def __init__(self):
        self.data = state['mock_boto_s3_multipart_upload_data']

    def upload_part_from_file(self, f, part_no, cb=None, num_cb=None):
        self.data.append(f.read())

    def complete_upload(self):
        pass

    def cancel_upload(self):
        pass


class MockBotoS3Bucket():
    def lookup(self, key):
        pass

    def initiate_multipart_upload(self, key):
        return MockBotoS3MultipartUpload()


class S3Connection():
    def __init__(self, key, secret, is_secure=None, host=None):
        pass

    def get_bucket(self, bucket_name):
        return MockBotoS3Bucket()
