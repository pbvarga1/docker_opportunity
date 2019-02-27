import json
from unittest import mock

import pytest
import requests
from flask import Response

from web import app
from web.pdsimage import PDSImage
app.app.config['TESTING'] = True


@pytest.fixture
def mock_requests():
    path = 'web.app.requests'
    with mock.patch(path, autospec=True) as mr:
        mr.exceptions.HTTPError = requests.exceptions.HTTPError
        yield mr


@pytest.fixture
def client():
    return app.app.test_client()


@pytest.fixture
def request_context():
    return app.app.test_request_context


@pytest.fixture(scope='module', autouse=True)
def api_url():
    path = 'web.app.API_URL'
    with mock.patch(path, ''):
        yield


def create_response(data):
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(data).encode()
    return response


@mock.patch('web.app.render_template', autospec=True)
def test_index(render_template, client):
    render_template.return_value = Response(200, 'fake')
    client.get('/')
    render_template.assert_called_once_with('index.html')


def test_create_resource(mock_requests, request_context):
    data = {'Name': 'foo', 'ID': 1}
    response = create_response(data)
    mock_requests.post.return_value = response
    with request_context(json={'name': 'foo'}):
        json_data = app._create_resource('product_types', True)
    mock_requests.post.assert_called_once_with(
        '/product_types',
        json={'Name': 'FOO'}
    )
    assert json_data == data

    response.status_code = 400
    with request_context(json={'name': 'foo'}):
        with pytest.raises(requests.exceptions.HTTPError):
            json_data = app._create_resource('product_types', True)


def test_get_resources(mock_requests):
    data = [{'Name': 'foo', 'ID': 1}, {'Name': 'bar', 'ID': 2}]
    response = create_response(data)
    mock_requests.get.return_value = response
    json_data = app._get_resources('product_types')
    assert json_data == data
    mock_requests.get.assert_called_once_with(
        '/product_types',
        params={'Active': True},
    )

    response.status_code = 400
    json_data = app._get_resources('product_types')
    assert json_data == []


@mock.patch('web.app._create_resource', autospec=True)
def test_create_product_type(_create_resource, client):
    data = {'Name': 'foo', 'ID': 1}
    _create_resource.return_value = data
    pt = client.post('/services/product_types', json={'name': 'foo'})
    _create_resource.assert_called_once_with('product_types', True)
    assert pt.json['data'] == data


@mock.patch('web.app._get_resources', autospec=True)
def test_get_product_types(_get_resources, client):
    data = [{'Name': 'foo', 'ID': 1}, {'Name': 'bar', 'ID': 2}]
    _get_resources.return_value = data
    r = client.get('/services/product_types')
    assert r.json == {'data': data}
    assert r.status_code == 200
    _get_resources.assert_called_once_with('product_types')


@mock.patch('web.app._create_resource', autospec=True)
def test_create_camera(_create_resource, client):
    data = {'Name': 'foo', 'ID': 1}
    _create_resource.return_value = data
    cam = client.post('/services/cameras', json={'name': 'foo'})
    _create_resource.assert_called_once_with('cameras', False)
    assert cam.json['data'] == data


@mock.patch('web.app._get_resources', autospec=True)
def test_get_cameras(_get_resources, client):
    data = [{'Name': 'foo', 'ID': 1}, {'Name': 'bar', 'ID': 2}]
    _get_resources.return_value = data
    r = client.get('/services/cameras')
    assert r.json == {'data': data}
    assert r.status_code == 200
    _get_resources.assert_called_once_with('cameras')


def test_register_image(mock_requests, client):
    response = create_response({'foo': 'bar'})
    mock_requests.post.return_value = response
    data = {
        'url': 'path/imagename.img',
        'sol': 42,
        'detatched': False,
        'productType': 1,
        'camera': 2,
    }
    r = client.post('/services/images', json=data)
    assert r.status_code == 200
    mock_requests.post.assert_called_once_with(
        '/images',
        json={
            'Name': 'imagename.img',
            'URL': 'path/imagename.img',
            'Sol': 42,
            'DetatchedLabel': False,
            'CameraID': 2,
            'ProductTypeID': 1,
        }
    )
    response.status_code = 400
    with pytest.raises(requests.exceptions.HTTPError):
        client.post('/services/images', json=data)


def test_get_images(mock_requests, client):
    response = create_response({'foo': 'bar'})
    mock_requests.get.return_value = response
    client.get('/services/images')
    mock_requests.get.assert_called_once_with(
        '/images',
        params={'Active': True}
    )
    response.status_code = 400
    with pytest.raises(requests.exceptions.HTTPError):
        client.get('/services/images')


@mock.patch('web.app.PDSImage', autospec=True)
def test_display_image(MockPDSImage, client):
    image = mock.create_autospec(PDSImage, instance=True)
    png_output = mock.MagicMock()
    png_output.getvalue.return_value = b'foo'
    image.get_png_output.return_value = png_output
    MockPDSImage.from_url.return_value = image
    r = client.get('/services/display_image?url=bar')
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'image/png'
    MockPDSImage.from_url.assert_called_once_with('bar')
    image.get_png_output.assert_called_once_with()
