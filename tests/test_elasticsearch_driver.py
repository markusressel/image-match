import hashlib
import os

import pytest

try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve
from elasticsearch import Elasticsearch, ConnectionError, RequestError, \
    NotFoundError
from time import sleep

from image_match.elasticsearch_driver import SignatureES
from PIL import Image

test_img_url1 = 'https://github.com/markusressel/image-match/blob/master/tests/images/clouds/IMG_20190903_193537.jpg?raw=true'
test_img_url2 = 'https://github.com/markusressel/image-match/blob/master/tests/images/clouds/IMG_20190903_193537-telegram-compression.jpg?raw=true'

test_img_filename_1 = "IMG_20190903_193537.jpg"
test_img_filename_2 = "IMG_20190903_193537-telegram-compression.jpg"
test_img_path_1 = f"./images/clouds/{test_img_filename_1}"
test_img_path_2 = f"./images/clouds/{test_img_filename_2}"

INDEX_NAME = 'test_environment_{}'.format(
    hashlib.md5(os.urandom(128)).hexdigest()[:12])
DOC_TYPE = '_doc'
MAPPINGS = {
    "mappings": {
        "properties": {
            DOC_TYPE: {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "metadata": {
                        "properties": {
                            "tenant_id": {
                                "type": "keyword",
                            }
                        }
                    }
                }
            }
        }
    }
}


@pytest.fixture(scope='module', autouse=True)
def index_name():
    return INDEX_NAME


@pytest.fixture(scope='function', autouse=True)
def setup_index(request, index_name):
    es = Elasticsearch()
    try:
        es.indices.create(index=index_name, body=MAPPINGS)
    except RequestError as e:
        if e.error == u'resource_already_exists_exception':
            es.indices.delete(index=index_name)
        else:
            raise

    def fin():
        try:
            es.indices.delete(index=index_name)
        except NotFoundError:
            pass

    request.addfinalizer(fin)


@pytest.fixture(scope='function', autouse=True)
def cleanup_index(request, es, index_name):
    def fin():
        try:
            es.indices.delete(index=index_name)
        except NotFoundError:
            pass

    request.addfinalizer(fin)


@pytest.fixture
def es():
    return Elasticsearch()


@pytest.fixture
def ses(es, index_name):
    return SignatureES(
        es=es,
        index=index_name,
        doc_type=DOC_TYPE
    )


def test_elasticsearch_running(es):
    i = 0
    while i < 5:
        try:
            es.ping()
            assert True
            return
        except ConnectionError:
            i += 1
            sleep(2)

    pytest.fail(
        f'Elasticsearch not running (failed to connect after {i} tries)'
    )


def test_add_image_by_url(ses):
    ses.add_image(path=test_img_url1)
    ses.add_image(path=test_img_url2)
    assert True


def test_add_image_by_path(ses):
    ses.add_image(path=test_img_path_1)
    assert True


def test_index_refresh(ses):
    ses.add_image(path=test_img_path_1, refresh_after=True)
    r = ses.search_image(path=test_img_path_1)
    assert len(r) == 1


def test_add_image_as_bytestream(ses):
    with open(test_img_path_1, 'rb') as f:
        ses.add_image(path='bytestream_test', img=f.read(), bytestream=True)
    assert True


def test_add_image_with_different_name(ses):
    ses.add_image(path='custom_name_test', img=test_img_path_1,
                  bytestream=False)
    assert True


def test_lookup_from_url(ses):
    ses.add_image(path=test_img_path_1, refresh_after=True)
    r = ses.search_image(path=test_img_url1)
    assert len(r) == 1
    assert r[0]['path'] == test_img_path_1
    assert 'score' in r[0]
    assert 'dist' in r[0]
    assert 'id' in r[0]


def test_lookup_from_file(ses):
    ses.add_image(path=test_img_path_1, refresh_after=True)
    r = ses.search_image(path=test_img_path_1)
    assert len(r) == 1
    assert r[0]['path'] == test_img_path_1
    assert 'score' in r[0]
    assert 'dist' in r[0]
    assert 'id' in r[0]


def test_lookup_from_bytestream(ses):
    ses.add_image(path=test_img_path_1, refresh_after=True)
    with open(test_img_path_1, 'rb') as f:
        r = ses.search_image(path=f.read(), bytestream=True)
    assert len(r) == 1
    assert r[0]['path'] == test_img_path_1
    assert 'score' in r[0]
    assert 'dist' in r[0]
    assert 'id' in r[0]


def test_lookup_with_cutoff(ses):
    ses.add_image(path=test_img_path_2, refresh_after=True)
    ses.distance_cutoff = 0.01
    r = ses.search_image(path=test_img_path_1)
    assert len(r) == 0


def test_distance_consistency(ses):
    ses.add_image(path=test_img_path_1)
    ses.add_image(path=test_img_path_2, refresh_after=True)
    r = ses.search_image(path=test_img_path_1)
    assert r[0]['dist'] == 0.0
    assert r[-1]['dist'] == 0.05310655950531569


def test_add_image_with_metadata(ses):
    metadata = {
        'some_info': {'test': 'ok!'}
    }
    ses.add_image(path=test_img_path_1, metadata=metadata, refresh_after=True)
    r = ses.search_image(path=test_img_path_1)
    assert r[0]['metadata'] == metadata
    assert 'path' in r[0]
    assert 'score' in r[0]
    assert 'dist' in r[0]
    assert 'id' in r[0]


def test_lookup_with_filter_by_metadata(ses):
    metadata = dict(
        tenant_id='foo'
    )
    ses.add_image(path=test_img_path_1, metadata=metadata, refresh_after=True)

    metadata2 = dict(
        tenant_id='bar-2'
    )
    ses.add_image(path=test_img_path_2, metadata=metadata2, refresh_after=True)

    r = ses.search_image(
        path=test_img_path_1,
        pre_filter={
            "term": {'{}.metadata.tenant_id'.format(DOC_TYPE): "foo"}
        }
    )
    assert len(r) == 1
    assert r[0]['metadata'] == metadata

    r = ses.search_image(
        path=test_img_path_1,
        pre_filter={
            "term": {'{}.metadata.tenant_id'.format(DOC_TYPE): "bar-2"}
        }
    )
    assert len(r) == 1
    assert r[0]['metadata'] == metadata2

    r = ses.search_image(
        path=test_img_path_1,
        pre_filter={
            "term": {'{}.metadata.tenant_id'.format(DOC_TYPE): "bar-3"}
        }
    )
    assert len(r) == 0


def test_all_orientations(ses):
    im = Image.open(test_img_path_1)
    rotated_test_img_path = 'rotated_test1.jpg'
    im.rotate(90, expand=True).save(rotated_test_img_path)

    ses.add_image(path=test_img_path_1, refresh_after=True)
    r = ses.search_image(path=rotated_test_img_path, all_orientations=True)
    assert len(r) == 1
    assert r[0]['path'] == test_img_path_1
    assert r[0]['dist'] < 0.05  # some error from rotation

    with open(rotated_test_img_path, 'rb') as f:
        r = ses.search_image(
            path=f.read(), bytestream=True,
            all_orientations=True
        )
        assert len(r) == 1
        assert r[0]['dist'] < 0.05  # some error from rotation

    # delete test file
    os.remove(rotated_test_img_path)


def test_duplicate(ses):
    ses.add_image(path=test_img_path_1, refresh_after=True)
    ses.add_image(path=test_img_path_1, refresh_after=True)
    r = ses.search_image(path=test_img_path_1)
    assert len(r) == 2
    assert r[0]['path'] == test_img_path_1
    assert 'score' in r[0]
    assert 'dist' in r[0]
    assert 'id' in r[0]


def test_duplicate_removal(ses):
    for i in range(10):
        ses.add_image(test_img_path_1)
    sleep(1)
    r = ses.search_image(test_img_path_1)
    assert len(r) == 10
    ses.delete_duplicates(test_img_path_1)
    sleep(1)
    r = ses.search_image(test_img_path_1)
    assert len(r) == 1
