from io import BytesIO
from unittest import mock

import pvl
import numpy as np

from web import pdsimage


def test_get_start_byte(label):
    assert pdsimage.PDSImage._get_start_byte(label) == 195
    label['^IMAGE'] = pvl.Units(5, 'BYTES')
    assert pdsimage.PDSImage._get_start_byte(label) == 5


def test_get_shape(label):
    assert pdsimage.PDSImage._get_shape(label) == (3, 2, 4)


@mock.patch('web.pdsimage.requests', autospect=True)
def test_from_url(mock_requests, image):
    response = mock.MagicMock()
    mock_requests.get.return_value = response
    print(image.label['^IMAGE'])
    print(len(pvl.dumps(image.label) + b'\r\n'))
    response.content = pvl.dumps(image.label) + b'\r\n' + image.data.tobytes()
    url = 'path/image.img'
    im = pdsimage.PDSImage.from_url(url)
    response.raise_for_status.assert_called_once_with()
    mock_requests.get.assert_called_with(url)
    np.testing.assert_array_equal(im.data, image.data)


@mock.patch('web.pdsimage.requests', autospect=True)
def test_from_url_detatched(mock_requests, image):
    image._label['^IMAGE'] = 1
    response1 = mock.MagicMock()
    response2 = mock.MagicMock()
    response1.content = image.data.tobytes()
    response2.content = pvl.dumps(image.label)
    mock_requests.get.side_effect = [response1, response2]
    url = 'path/image.img'
    im = pdsimage.PDSImage.from_url(url, detatched=True)
    np.testing.assert_array_equal(im.data, image.data)
    mock_requests.get.assert_has_calls([
        mock.call(url),
        mock.call('path/image.lbl'),
    ])
    response1.raise_for_status.assert_called_once_with()
    response2.raise_for_status.assert_called_once_with()


def test_data(image):
    assert image.data is not image._data
    np.testing.assert_array_equal(image.data, image._data)


def test_label(image):
    assert image.label is not image._label
    assert image.label == image._label


def test_bands(image, gray_image):
    assert image.bands == 3
    assert gray_image.bands == 1


def test_image(image, gray_image):
    assert image.image.shape == (2, 4, 3)
    assert gray_image.image.shape == (2, 4)


def test_get_png_output(image, gray_image):
    assert isinstance(image.get_png_output(), BytesIO)
    assert b'PNG' in image.get_png_output().getvalue()
    assert b'PNG' in gray_image.get_png_output().getvalue()
