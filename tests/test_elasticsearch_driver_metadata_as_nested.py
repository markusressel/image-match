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
                            "tenant_id": {"type": "keyword"},
                            "project_id": {"type": "keyword"}
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
        if e.error == u'index_already_exists_exception':
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
        el_version=7,
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

    pytest.fail('Elasticsearch not running (failed to connect after {} tries)'
                .format(str(i)))


def test_lookup_with_filter_by_metadata(ses):
    ses.add_image(
        test_img_path_1, metadata=_metadata('foo', 'project-x'),
        refresh_after=True
    )
    ses.add_image(
        test_img_path_2, metadata=_metadata('foo', 'project-x'),
        refresh_after=True
    )
    ses.add_image(
        'test3.jpg', img=test_img_path_1,
        metadata=_metadata('foo', 'project-y'), refresh_after=True
    )

    ses.add_image(
        test_img_path_2, metadata=_metadata('bar', 'project-x'),
        refresh_after=True
    )

    r = ses.search_image(
        test_img_path_1,
        pre_filter=_nested_filter('foo', 'project-x')
    )
    assert len(r) == 2

    r = ses.search_image(
        test_img_path_1,
        pre_filter=_nested_filter('foo', 'project-z')
    )
    assert len(r) == 0

    r = ses.search_image(
        test_img_path_1,
        pre_filter=_nested_filter('bar', 'project-x')
    )
    assert len(r) == 1

    r = ses.search_image(
        test_img_path_1,
        pre_filter=_nested_filter('bar-2', 'project-x')
    )
    assert len(r) == 0

    r = ses.search_image(
        test_img_path_1,
        pre_filter=_nested_filter('bar', 'project-z')
    )
    assert len(r) == 0


def _metadata(tenant_id, project_id):
    return dict(
        tenant_id=tenant_id,
        project_id=project_id
    )


def _nested_filter(tenant_id, project_id):
    return [
        {"term": {"image.metadata.tenant_id": tenant_id}},
        {"term": {"image.metadata.project_id": project_id}}
    ]
