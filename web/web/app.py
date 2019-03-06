import posixpath
from typing import Tuple, List, Any, Awaitable

import aiohttp
from quart import (
    Quart,
    jsonify,
    request,
    Response,
    Blueprint,
    make_response,
    render_template,
)

from web.pdsimage import PDSImage
from web.redis_cache import ImageCache, get_rcache


class SessionQuart(Quart):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: aiohttp.ClientSession = None


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
    return await render_template('index.html')


async def _create_resource(resource_name: str,
                           is_upper: bool) -> Tuple[dict, int]:
    url = f'{API_URL}/{resource_name}'
    try:
        request_json = await request.get_json()
        name = request_json['name']
        if is_upper:
            name = name.upper()
        data = {'Name': name}
    except KeyError:
        return {'error': 'json format should be {"name": "<value>"}'}, 400
    async with app.session.post(url, json=data) as resp:
        data = await resp.json()
    return data, resp.status


async def _get_resources(resource_name: str) -> Tuple[List[Any], int]:
    url = f'{API_URL}/{resource_name}'
    params = {'Active': 'true'}
    try:
        async with app.session.get(url, params=params) as resp:
            resources = await resp.json()
            status_code = resp.status
    except aiohttp.ClientResponseError as err:
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
    async with app.session.post(f'{API_URL}/images', json=new_image) as resp:
        data = await resp.json()
        status_code = resp.status
    return jsonify(data=data), status_code


@services.route('/images', methods=['GET'])
async def get_images() -> Tuple[Response, int]:
    params = {'Active': 'true'}
    async with app.session.get(f'{API_URL}/images', params=params) as resp:
        data = await resp.json()
        status_code = resp.status
    return jsonify(data=data), status_code


@services.route('/display_image', methods=['GET'])
async def display_image() -> Response:
    rcache = await get_rcache()
    image_cache = ImageCache(rcache)
    url = request.args['url']
    name = posixpath.basename(url)
    cache_future: Awaitable[Any]
    if await image_cache.exists(name):
        image = await image_cache.get(name)
        cache_future = image_cache.set_time(name)
    else:
        image = await PDSImage.from_url(url, session=app.session)
        cache_future = image_cache.set(name, image)
    png_output = await image.get_png_output()
    response = await make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    await cache_future
    return response


app.register_blueprint(services, url_prefix='/services')
