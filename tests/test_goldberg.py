import pytest
from numpy import ndarray, array_equal
try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve

from image_match.goldberg import ImageSignature, CorruptImageError

test_img_url = 'https://github.com/markusressel/image-match/blob/master/tests/images/clouds/IMG_20190903_193537.jpg?raw=true'
test_diff_img_url = 'https://github.com/markusressel/image-match/blob/master/tests/images/clouds/IMG_20190903_193537-telegram-compression.jpg?raw=true'

test_img_filename_1 = "IMG_20190903_193537.jpg"
test_img_filename_2 = "IMG_20190903_193537-telegram-compression.jpg"
test_img_path_1 = f"./images/clouds/{test_img_filename_1}"
test_img_path_2 = f"./images/clouds/{test_img_filename_2}"

def test_load_from_url():
    gis = ImageSignature()
    sig = gis.generate_signature(test_img_url)
    assert type(sig) is ndarray
    assert sig.shape == (648,)


def test_load_from_file():
    gis = ImageSignature()
    sig = gis.generate_signature(test_img_path_1)
    assert type(sig) is ndarray
    assert sig.shape == (648,)


def test_load_from_unicode_path():
    try:
        path = test_img_path_1
    except NameError:
        return
    gis = ImageSignature()
    sig = gis.generate_signature(path)
    assert type(sig) is ndarray
    assert sig.shape == (648,)


def test_load_from_stream():
    gis = ImageSignature()
    with open(test_img_path_1, 'rb') as f:
        sig = gis.generate_signature(f.read(), bytestream=True)
        assert type(sig) is ndarray
        assert sig.shape == (648,)


def test_load_from_corrupt_stream():
    gis = ImageSignature()
    with pytest.raises(CorruptImageError):
        gis.generate_signature(b'corrupt', bytestream=True)


def test_all_inputs_same_sig():
    gis = ImageSignature()
    sig1 = gis.generate_signature(test_img_url)
    sig2 = gis.generate_signature(test_img_path_1)
    with open(test_img_path_1, 'rb') as f:
        sig3 = gis.generate_signature(f.read(), bytestream=True)

    assert array_equal(sig1, sig2)
    assert array_equal(sig2, sig3)


def test_identity():
    gis = ImageSignature()
    sig = gis.generate_signature(test_img_path_1)
    dist = gis.normalized_distance(sig, sig)
    assert dist == 0.0


def test_difference():
    gis = ImageSignature()
    sig1 = gis.generate_signature(test_img_path_1)
    sig2 = gis.generate_signature(test_diff_img_url)
    dist = gis.normalized_distance(sig1, sig2)
    assert dist == 0.424549547059671
