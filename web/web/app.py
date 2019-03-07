import json
import asyncio
import posixpath
from typing import Tuple, List, Any

import logging
import aiohttp
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from quart import (
    Quart,
    jsonify,
    request,
    Response,
    Blueprint,
    make_response,
    render_template,
)

from web.constants import DSN
from web.pdsimage import PDSImage
from web.redis_cache import ImageCache, get_rcache, ProgressCache

logger = logging.getLogger(__name__)


class SessionQuart(Quart):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: aiohttp.ClientSession = None


sentry_sdk.init(
    dsn=DSN,
    integrations=[AioHttpIntegration()],
)


app = SessionQuart(__name__)

services = Blueprint('services', __name__)

API_URL = 'http://opp-app:80/api'


@app.before_serving
async def before_serving():
    session = aiohttp.ClientSession(raise_for_status=True)
    app.session = session


@app.after_serving
async def after_serving():
    await app.session.close()


@app.route('/')
@app.route('/cameras')
@app.route('/product_types')
async def index() -> str:
    return await render_template('index.html', DSN=DSN)


async def _create_resource(resource_name: str,
                           is_upper: bool) -> Tuple[dict, int]:
    url = f'{API_URL}/{resource_name}'
    try:
        request_json = await request.get_json()
        name = request_json['name']
        if is_upper:
            name = name.upper()
        data = {'Name': name}
        logger.info(f'Creating resource {resource_name} with name {name}')
    except KeyError:
        logger.exception('json format should be {"name": "<value>"}')
        return {'error': 'json format should be {"name": "<value>"}'}, 400
    try:
        async with app.session.post(url, json=data) as resp:
            data = await resp.json()
    except aiohttp.ClientResponseError as err:
        logger.exception(f'Error creating resource {resource_name}')
        return {'error': str(err)}, err.status
    return data, resp.status


async def _get_resources(resource_name: str) -> Tuple[List[Any], int]:
    url = f'{API_URL}/{resource_name}'
    params = {'Active': 'true'}
    logger.info(f'GET {url}')
    try:
        async with app.session.get(url, params=params) as resp:
            resources = await resp.json()
            status_code = resp.status
    except aiohttp.ClientResponseError as err:
        logger.exception(f'Failed getting resource {resource_name}')
        return [], err.status
    return resources, status_code


@services.route('/product_types', methods=['POST'])
async def create_product_type() -> Tuple[Response, int]:
    product_type, status_code = await _create_resource('product_types', True)
    return jsonify(data=product_type), status_code


@services.route('/product_types', methods=['GET'])
async def get_product_types() -> Tuple[Response, int]:
    product_types, status_code = await _get_resources('product_types')
    return jsonify(data=product_types), status_code


@services.route('/cameras', methods=['POST'])
async def create_camera() -> Tuple[Response, int]:
    camera, status_code = await _create_resource('cameras', False)
    return jsonify(data=camera), status_code


@services.route('/cameras', methods=['GET'])
async def get_cameras() -> Tuple[Response, int]:
    cameras, status_code = await _get_resources('cameras')
    return jsonify(data=cameras), status_code


@services.route('/images', methods=['POST'])
async def register_image() -> Tuple[Response, int]:
    data = await request.get_json()
    sol = int(data['sol'])
    url = str(data['url'])
    name = posixpath.basename(url)
    detatched = bool(data['detatched'])
    product_type_id = int(data['productType'])
    camera_id = int(data['camera'])
    new_image = {
        'Name': name,
        'URL': url,
        'Sol': sol,
        'DetatchedLabel': detatched,
        'CameraID': camera_id,
        'ProductTypeID': product_type_id,
    }
    api_url = f'{API_URL}/images'
    logger.info(f'POST {api_url} - data: {json.dumps(new_image)}')
    try:
        async with app.session.post(api_url, json=new_image) as resp:
            data = await resp.json()
            status_code = resp.status
    except aiohttp.ClientResponseError as err:
        logger.exception(f'Failed creating image with error {str(err)}')
        data = {}
        status_code = err.status
    return jsonify(data=data), status_code


@services.route('/images', methods=['GET'])
async def get_images() -> Tuple[Response, int]:
    params = {'Active': 'true'}
    rcache = await get_rcache()
    image_cache = ImageCache(rcache)

    async def is_cached(im):
        im['cached'] = await image_cache.exists(im['Name'])
        return im

    api_url = f'{API_URL}/images'
    logger.info('GET api_url')
    async with app.session.get(api_url, params=params) as resp:
        data = await resp.json()
        data = await asyncio.gather(*[is_cached(im) for im in data])
        data = list(sorted(data, key=lambda im: im['ID'], reverse=True))
        status_code = resp.status
    return jsonify(data=data), status_code


@services.route('/cache_image', methods=['POST'])
async def cache_image() -> Tuple[Response, int]:
    rcache = await get_rcache()
    image_cache = ImageCache(rcache)
    data = await request.get_json()
    url = data['url']
    name = data['name']
    if await image_cache.exists(name):
        return jsonify({'data': 'finished'}), 200
    else:
        logger.info(f'Cacheing Image: {name}')
        progress_cache = ProgressCache(rcache)
        image = await PDSImage.from_url(
            url=url,
            session=app.session,
            progress=(progress_cache, name),
        )
        await image_cache.set(name, image)
        return jsonify({'data': 'finished'}), 200


@services.route('/display_image', methods=['GET'])
async def display_image() -> Response:
    rcache = await get_rcache()
    image_cache = ImageCache(rcache)
    url = request.args['url']
    name = posixpath.basename(url)
    logger.info(f'Displaying Image: {name}')
    image = await image_cache.get(name)
    cache_future = image_cache.set_time(name)
    png_output = await image.get_png_output()
    response = await make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    await cache_future
    return response


@services.route('/progress', methods=['POST'])
async def get_progress():
    rcache = await get_rcache()
    data = await request.get_json()
    ID = data['ID']
    progress_cache = ProgressCache(rcache)
    progress = await progress_cache.get(str(ID))
    logger.info(f'Progress: {name}: {progress * 100}%')
    return jsonify({'data': progress})


app.register_blueprint(services, url_prefix='/services')
