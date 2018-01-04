# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import pytest

import google.cloud.exceptions
import google.cloud.storage

import inspect_gcs_file

GCLOUD_PROJECT = os.getenv('GCLOUD_PROJECT')
TEST_BUCKET_NAME = GCLOUD_PROJECT + '-dlp-python-client-test'
RESOURCE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'resources')
RESOURCE_FILE_NAMES = ['test.txt', 'test.png', 'harmless.txt', 'accounts.txt']


@pytest.fixture(scope='module')
def bucket(request):
    # Creates a GCS bucket, uploads files required for the test, and tears down
    # the entire bucket afterwards.

    client = google.cloud.storage.Client()
    try:
        bucket = client.get_bucket(TEST_BUCKET_NAME)
    except google.cloud.exceptions.NotFound:
        bucket = client.create_bucket(TEST_BUCKET_NAME)

    # Upoad the blobs and keep track of them in a list.
    blobs = []
    for name in RESOURCE_FILE_NAMES:
        path = os.path.join(RESOURCE_DIRECTORY, name)
        blob = bucket.blob(name)
        blob.upload_from_filename(path)
        blobs.append(blob)

    # Yield the object to the test code; lines after this execute as a teardown.
    yield bucket

    # Delete the files.
    for blob in blobs:
        blob.delete()

    # Attempt to delete the bucket; this will only work if it is empty.
    bucket.delete()

    print('teardown complete')


def test_inspect_gcs_file(bucket, capsys):
    inspect_gcs_file.inspect_gcs_file(bucket.name, 'test.txt')

    out, _ = capsys.readouterr()
    assert 'Info type: EMAIL_ADDRESS' in out


def test_inspect_gcs_file_with_info_types(bucket, capsys):
    inspect_gcs_file.inspect_gcs_file(
        bucket.name, 'test.txt', info_types=['EMAIL_ADDRESS'])

    out, _ = capsys.readouterr()
    assert 'Info type: EMAIL_ADDRESS' in out


def test_inspect_gcs_file_no_results(bucket, capsys):
    inspect_gcs_file.inspect_gcs_file(bucket.name, 'harmless.txt')

    out, _ = capsys.readouterr()
    assert 'No findings' in out


def test_inspect_gcs_image_file(bucket, capsys):
    inspect_gcs_file.inspect_gcs_file(bucket.name, 'test.png')

    out, _ = capsys.readouterr()
    assert 'Info type: EMAIL_ADDRESS' in out

def test_inspect_gcs_multiple_file(bucket, capsys):
    inspect_gcs_file.inspect_gcs_file(bucket.name, '*')

    out, _ = capsys.readouterr()
    assert 'Info type: PHONE_NUMBER' in out
    assert 'Info type: CREDIT_CARD' in out
