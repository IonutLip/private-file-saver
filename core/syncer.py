import glob
from os.path import isfile

from botocore.exceptions import ClientError

from core.configs import *
from core.log_utils import logger
from core.s3_client import S3Client
from core.utils import calc_md5sum


class Syncer:
    def __init__(self):
        self.target_path = TARGET_PATH
        self.bucket_name = DEFAULT_BUCKET_NAME
        self.client = S3Client(self.bucket_name)
        self.CHUNK_SIZE = 4 * 1024 * 1024
        self.dry_run = False

    def sync(self, dry_run=True, recursive=True):
        """
        Scan the directory of interest
        """
        self.dry_run = dry_run
        logger.info("Dry run is {}".format("on" if dry_run else "off"))

        if not self.bucket_name:
            raise AssertionError("Bucket name is missing.")

        target_directory = os.path.abspath(TARGET_PATH)
        logger.info(f"Target directory: {target_directory}")
        os.chdir(target_directory)

        files_iter = glob.iglob("**", recursive=recursive)
        for file in files_iter:
            if isfile(file):
                md5sum_local = calc_md5sum(file)

                # File not in Bucket
                if not self._is_object_exists(file):
                    logger.debug("File doesn't exist, uploading.. ({})".format(file))
                    self._upload_file(file, md5sum=md5sum_local)
                else:
                    # File is in Bucket
                    metadata_remote = self._get_object_metadata(file)
                    md5sum_remote = metadata_remote.get('md5sum', None)
                    if md5sum_local != md5sum_remote:  # Upload file if sync required
                        logger.info("Etags mismatched. File is being uploaded ({})".format(file))
                        self._upload_file(file, md5sum_local)

    def _is_object_exists(self, rel_file_path) -> bool:
        try:
            self._get_object_metadata(rel_file_path=rel_file_path)
        except ClientError as e:
            if e.response["Error"]["Code"] == '404':
                return False
            raise e
        else:
            return True

    def _upload_file(self, file, md5sum):
        if self.dry_run:
            return

        self.client.put_object(object_key=file, file_path=file, metadata={'md5sum': md5sum})

    def _get_object_metadata(self, rel_file_path):
        return self.client.get_object(object_key=rel_file_path).metadata

    def set_bucket_name(self, bucket_name):
        logger.debug("Setting bucket name to {}".format(bucket_name))
        self.bucket_name = bucket_name
        self._reinitialize_client()

    def _reinitialize_client(self):
        logger.debug("Reinitializing S3Client, probably due to new bucket_name")
        self.client = S3Client(self.bucket_name)