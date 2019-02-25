import json
from unittest import mock
from werkzeug.exceptions import BadRequest

import pytest
import requests

from web.app import app
app.config['TESTING'] = True


@pytest.fixture
def mock_requests():
    path = 'web.app.requests'
    with mock.patch(path, autospec=True) as mr:
        mr.exceptions.HTTPError = requests.exceptions.HTTPError
        yield mr


@pytest.fixture
def client():
    return app.test_client()


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


def test_create_product_type(mock_requests, client):
    data = {'Name': 'foo', 'ID': 1}
    response = create_response(data)
    mock_requests.post.return_value = response
    r = client.post('/product_types', json={'name': 'foo'})
    mock_requests.post.assert_called_once_with(
        '/product_types',
        json={'Name': 'FOO'}
    )
    assert r.status_code == 200
    assert r.json == {'product_type': data}
    r = client.post('/product_types', json={'nam': 'foo'})
    assert r.status_code == 400

    with pytest.raises(requests.exceptions.HTTPError):
        response.status_code = 400
        client.post('/product_types', json={'name': 'foo'})


def test_get_product_types(mock_requests, client):
    data = [{'Name': 'foo', 'ID': 1}, {'Name': 'bar', 'ID': 2}]
    response = create_response(data)
    mock_requests.get.return_value = response
    r = client.get('/product_types')
    assert r.json == {'names': ['foo', 'bar']}
    assert r.status_code == 200
    mock_requests.get.assert_called_once_with(
        '/product_types',
        params={'Active': True},
    )
    response.status_code = 400
    r = client.get('/product_types')
    assert r.json == {'names': []}
    assert r.status_code == 200
