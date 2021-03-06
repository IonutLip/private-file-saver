import boto3
from boto3 import Session
from boto3.s3.transfer import TransferConfig

from core.configs import configs


class S3Client:
    def __init__(self, bucket_name=None):
        _credentials = {
            "aws_access_key_id": configs.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": configs.AWS_SECRET_ACCESS_KEY,
            "region_name": configs.AWS_REGION
        }

        self.bucket_name = bucket_name
        self.transfer_config = TransferConfig(multipart_threshold=configs.MULTIPART_THRESHOLD,
                                              max_concurrency=configs.MAX_CONCURRENCY,
                                              multipart_chunksize=configs.MULTIPART_CHUNKSIZE)
        self.s3 = boto3.resource('s3', **_credentials)

    def set_bucket_name(self, bucket_name):
        self.bucket_name = bucket_name

    def list_regions(self):
        """
        FIXME improve this to show human readable region name
        """
        return Session().get_available_regions('s3')

    def list_buckets(self):
        return [bucket.name for bucket in self.s3.buckets.all()]

    def list_objects(self):
        return self.s3.Bucket(self.bucket_name).objects.all()

    def get_object(self, object_key):
        return self.s3.Object(bucket_name=self.bucket_name, key=object_key)

    def put_object(self, object_key, file_path, metadata) -> None:
        self.s3.Object(bucket_name=self.bucket_name, key=object_key) \
            .upload_file(file_path, Config=self.transfer_config, ExtraArgs={"Metadata": metadata})

    def download_object(self, object_key, file_path):
        # Make sure subdirectories exist before downloading
        self.s3.Bucket(self.bucket_name).download_file(Key=object_key, Filename=file_path)
