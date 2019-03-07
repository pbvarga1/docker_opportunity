import copy
from time import sleep

import pytest
import aiohttp

from web import app
from web.redis_cache import ImageCache
app.app.config['TESTING'] = True

PRODUCT_TYPES = [
    {'ID': 1, 'Name': 'EDR'},
    {'ID': 2, 'Name': 'RDR'}
]
IMAGES = [
    {'ID': 1, 'Name': 'im1'},
    {'ID': 2, 'Name': 'im2'},
]
CAMERAS = [
    {'ID': 1, 'Name': 'pancam'},
    {'ID': 2, 'Name': 'navcam'}
]


async def error(request):
    return aiohttp.web.json_response(['ERROR'], status=404)


async def get_cameras(request):
    return aiohttp.web.json_response(CAMERAS)


async def get_images(request):
    return aiohttp.web.json_response(IMAGES)


async def get_product_types(request):
    return aiohttp.web.json_response(PRODUCT_TYPES)


async def post_resource(request):
    try:
        data = await request.json()
        data['Created'] = True
        return aiohttp.web.json_response(data)
    except TypeError:
        return request


@pytest.fixture(scope='function')
async def cli(mocker, loop, aiohttp_client):
    ioapp = aiohttp.web.Application()
    ioapp.router.add_get('/api/images', get_images)
    ioapp.router.add_get('/api/product_types', get_product_types)
    ioapp.router.add_get('/api/cameras', get_cameras)
    ioapp.router.add_post('/api/cameras', post_resource)
    ioapp.router.add_post('/api/product_types', post_resource)
    ioapp.router.add_post('/api/images', post_resource)
    client = await aiohttp_client(ioapp, raise_for_status=True)
    mocker.patch('web.app.app.session', client)
    mocker.patch('web.app.API_URL', '/api')
    return client


@pytest.fixture
async def error_cli(mocker, loop, aiohttp_client):
    ioapp = aiohttp.web.Application()
    ioapp.router.add_get('/api/images', error)
    ioapp.router.add_get('/api/product_types', error)
    ioapp.router.add_get('/api/cameras', error)
    ioapp.router.add_post('/api/cameras', error)
    ioapp.router.add_post('/api/product_types', error)
    ioapp.router.add_post('/api/images', error)
    client = await aiohttp_client(ioapp, raise_for_status=True)
    mocker.patch('web.app.app.session', client)
    mocker.patch('web.app.API_URL', 'api')
    return client


@pytest.fixture
async def client():
    return app.app.test_client()


async def test_index(mocker, client, cli):
    render_template = mocker.patch('web.app.render_template', autospec=True)

    async def make_response(*args, **kwargs):
        return aiohttp.web.Response(status=200)
    render_template.side_effect = make_response
    for route in ['', 'cameras', 'product_types']:
        await client.get(f'/{route}')
        render_template.assert_called_with('index.html')


async def test_create_product_type(client, cli):
    expected = {'Name': 'FOO', 'Created': True}
    resp = await client.post('/services/product_types', json={'name': 'foo'})
    assert resp.status_code == 200
    assert await resp.get_json() == {'data': expected}
    resp = await client.post('/services/product_types', json={'nam': 'foo'})
    assert resp.status_code == 400
    assert await resp.get_json() == {
        'data': {'error': 'json format should be {"name": "<value>"}'}
    }


async def test_get_product_types(client, cli):
    resp = await client.get('/services/product_types')
    assert resp.status_code == 200
    assert await resp.get_json() == {'data': PRODUCT_TYPES}


async def test_get_product_types_error(client, error_cli):
    resp = await client.get('/services/product_types')
    assert resp.status_code == 404
    assert await resp.get_json() == {'data': []}


async def test_create_camera(client, cli):
    expected = {'Name': 'image', 'Created': True}
    resp = await client.post('/services/cameras', json={'name': 'image'})
    assert resp.status_code == 200
    assert await resp.get_json() == {'data': expected}
    resp = await client.post('/services/cameras', json={'nam': 'image'})
    assert resp.status_code == 400
    assert await resp.get_json() == {
        'data': {'error': 'json format should be {"name": "<value>"}'}
    }


async def test_get_cameras(client, cli):
    resp = await client.get('/services/cameras')
    assert resp.status_code == 200
    assert await resp.get_json() == {'data': CAMERAS}


async def test_get_cameras_error(client, error_cli):
    resp = await client.get('/services/cameras')
    assert resp.status_code == 404
    assert await resp.get_json() == {'data': []}


async def test_register_image(client, cli):
    data = {
        'url': 'path/imagename.img',
        'sol': 42,
        'detatched': False,
        'productType': 1,
        'camera': 2,
    }
    resp = await client.post('/services/images', json=data)
    assert resp.status_code == 200
    expected = {
        'Name': 'imagename.img',
        'URL': 'path/imagename.img',
        'Sol': 42,
        'DetatchedLabel': False,
        'CameraID': 2,
        'ProductTypeID': 1,
        'Created': True,
    }
    assert await resp.get_json() == {'data': expected}


async def test_get_images(client, cli, mocker, rcache):
    mock_get = mocker.spy(cli, 'get')
    resp = await client.get('/services/images')
    mock_get.assert_called_once_with(
        '/api/images',
        params={'Active': 'true'}
    )
    assert resp.status_code == 200
    c1, c2 = copy.deepcopy(IMAGES)
    c1['cached'] = False
    c2['cached'] = False
    assert await resp.get_json() == {'data': [c2, c1]}


async def test_display_image(client, rcache, image, mocker, cli):

    async def from_url(*args, **kwargs):
        return image
    mock_from_url = mocker.patch(
        'web.app.PDSImage.from_url',
        side_effect=from_url,
    )
    r = await client.get('/services/display_image?url=path/image.img')
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'image/png'
    mock_from_url.assert_called_once_with('path/image.img', session=cli)
    assert (await image.get_png_output()).getvalue() == await r.get_data()
    image_cache = ImageCache(rcache)
    assert await image_cache.exists('image.img')
    time_stamp = await image_cache.get_time('image.img')
    sleep(1)
    r = await client.get('/services/display_image?url=path/image.img')
    assert r.status_code == 200
    assert r.headers['Content-Type'] == 'image/png'
    # Make sure not called again
    assert mock_from_url.call_count == 1
    assert (await image.get_png_output()).getvalue() == await r.get_data()
    assert time_stamp != await image_cache.get_time('image.img')
