import posixpath

import aiohttp
from quart import (
    abort,
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

app = Quart(__name__)
app.url_map.strict_slashes = False

services = Blueprint('services', __name__)

API_URL = 'http://opp-app:80/api'


@app.route('/')
@app.route('/cameras')
@app.route('/product_types')
async def index() -> Response:
    return render_template('index.html')


async def _create_resource(resource_name: str, is_upper: bool) -> dict:
    url = f'{API_URL}/{resource_name}'
    try:
        name = request.json['name']
        if is_upper:
            name = name.upper()
        data = {'Name': name}
    except KeyError:
        abort(400, 'json format should be {"name": "<value>"')
    async with app.session.post(url, json=data) as resp:
        data = await resp.json()
    return data


async def _get_resources(resource_name: str) -> list:
    url = f'{API_URL}/{resource_name}'
    params = {'Active': True}
    try:
        async with app.session.get(url, params=params) as resp:
            resources = await resp.json()
    except aiohttp.ClientResponseError:
        return []
    return resources


@services.route('/product_types', methods=['POST'])
async def create_product_type() -> Response:
    product_type = await _create_resource('product_types', True)
    return jsonify(data=product_type)


@services.route('/product_types', methods=['GET'])
async def get_product_types() -> Response:
    product_types = await _get_resources('product_types')
    return jsonify(data=product_types)


@services.route('/cameras', methods=['POST'])
async def create_camera() -> Response:
    camera = await _create_resource('cameras', False)
    return jsonify(data=camera)


@services.route('/cameras', methods=['GET'])
async def get_cameras() -> Response:
    cameras = await _get_resources('cameras')
    return jsonify(data=cameras)


@services.route('/images', methods=['POST'])
async def register_image() -> Response:
    data = request.json
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
    return jsonify(data=data)


@services.route('/images', methods=['GET'])
async def get_images() -> Response:
    params = {'Active': True}
    async with app.session.get(f'{API_URL}/images', params=params) as resp:
        data = await resp.json()
    return jsonify(data=data)


@services.route('/display_image', methods=['GET'])
async def display_image() -> Response:
    rcache = get_rcache()
    image_cache = ImageCache(rcache)
    url = request.args['url']
    name = posixpath.basename(url)
    if name in image_cache:
        image = await image_cache[name]
        cache_future = image_cache.set_time(name)
    else:
        image = await PDSImage.from_url(url, app.session)
        cache_future = image_cache[name] = image
    png_output = image.get_png_output()
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    await cache_future
    return response


app.register_blueprint(services, url_prefix='/services')
