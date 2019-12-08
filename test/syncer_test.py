import os
import boto3
from moto import mock_s3

from core.aws.s3 import S3Client
from core.syncer import Syncer
from core.utils import calc_md5sum
from test.constants import REGION_NAME, BUCKET_NAME


def create_random_files(tmpdirname, num_of_files=10):
    """
    Create random files in dir given
    """
    os.chdir(tmpdirname)
    _files_created = []

    # Create random files
    for i in range(1, num_of_files + 1):
        _object_key = f"{i}{i}{i}.txt"
        _test_file = f"./{_object_key}"
        with open(_test_file, "w") as f:
            f.write("XXXXXXXXXXX")
        _files_created.append(_object_key)

    return _files_created


@mock_s3
def test_scan_files(tmpdir):
    s3 = boto3.resource('s3', region_name=REGION_NAME)
    s3.create_bucket(Bucket=BUCKET_NAME)
    client = S3Client(BUCKET_NAME)
    syncer = Syncer(BUCKET_NAME)

    _files_uploaded = []
    _num_of_file_uploaded = 0

    # Create random files
    _files_created = create_random_files(tmpdir)
    i = 0
    for file_name in _files_created:
        # Upload some of this files
        if i % 2 == 0:
            _num_of_file_uploaded += 1
            _files_uploaded.append(file_name)
            client.put_object(object_key=file_name, file_path=file_name,
                              metadata={'md5sum': calc_md5sum(file_name)})

        # Modify one uploaded file
        if i == 6:
            # Modify file `666.txt`
            with open(file_name, "w") as f:
                f.write("yyyyyyyyyyyy")

        i += 1

    assert len(list(client.list_objects())) == 5 == _num_of_file_uploaded

    files = syncer.scan(tmpdir)

    # Assertion
    for file in files:
        assert file[1] == 'FILE'

        if file[0] == "666.txt":
            assert file[2] == 'NOT_SYNCED'
        elif file[0] in _files_uploaded:
            assert file[2] == 'SYNCED'
        else:
            assert file[2] == 'NOT_UPLOADED'

    num_of_file_synced = len(list(filter(lambda x: x[2] == 'SYNCED', files)))
    assert num_of_file_synced == 4


@mock_s3
def test_sync(tmpdir):
    s3 = boto3.resource('s3', region_name=REGION_NAME)
    s3.create_bucket(Bucket=BUCKET_NAME)
    _syncer = Syncer(BUCKET_NAME)
    _files_created = create_random_files(tmpdir)

    # Assert files created are not uploaded
    files = _syncer.scan(tmpdir)
    for file in files:
        assert file[1] == 'FILE'
        assert file[2] == 'NOT_UPLOADED'

    # Sync/upload files
    _syncer.sync(tmpdir)

    files = _syncer.scan(tmpdir)
    for file in files:
        assert file[1] == 'FILE'
        assert file[2] == 'UPLOADED'
