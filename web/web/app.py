import posixpath

import requests
from flask import (
    abort,
    Flask,
    jsonify,
    request,
    Response,
    Blueprint,
    make_response,
    render_template,
)

from web.pdsimage import PDSImage
from web.redis_cache import ImageCache, get_rcache

app = Flask(__name__)
app.url_map.strict_slashes = False

services = Blueprint('services', __name__)

API_URL = 'http://opp-app:80/api'


@app.route('/')
@app.route('/cameras')
@app.route('/product_types')
def index() -> Response:
    return render_template('index.html')


def _create_resource(resource_name: str, is_upper: bool) -> dict:
    url = f'{API_URL}/{resource_name}'
    try:
        name = request.json['name']
        if is_upper:
            name = name.upper()
        data = {'Name': name}
    except KeyError:
        abort(400, 'json format should be {"name": "<value>"')
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()


def _get_resources(resource_name: str) -> list:
    url = f'{API_URL}/{resource_name}'
    params = {'Active': True}
    response = requests.get(url, params=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        return []
    resources = response.json()
    return resources


@services.route('/product_types', methods=['POST'])
def create_product_type() -> Response:
    product_type = _create_resource('product_types', True)
    return jsonify(data=product_type)


@services.route('/product_types', methods=['GET'])
def get_product_types() -> Response:
    product_types = _get_resources('product_types')
    return jsonify(data=product_types)


@services.route('/cameras', methods=['POST'])
def create_camera() -> Response:
    camera = _create_resource('cameras', False)
    return jsonify(data=camera)


@services.route('/cameras', methods=['GET'])
def get_cameras() -> Response:
    cameras = _get_resources('cameras')
    return jsonify(data=cameras)


@services.route('/images', methods=['POST'])
def register_image() -> Response:
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
    r = requests.post(f'{API_URL}/images', json=new_image)
    r.raise_for_status()
    return jsonify(data=r.json())


@services.route('/images', methods=['GET'])
def get_images() -> Response:
    params = {'Active': True}
    r = requests.get(f'{API_URL}/images', params=params)
    r.raise_for_status()
    return jsonify(data=r.json())


@services.route('/display_image', methods=['GET'])
def display_image() -> Response:
    rcache = get_rcache()
    image_cache = ImageCache(rcache)
    url = request.args['url']
    name = posixpath.basename(url)
    if name in image_cache:
        image = image_cache[name]
        image_cache.set_time(name)
    else:
        image = PDSImage.from_url(url)
        image_cache[name] = image
    png_output = image.get_png_output()
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


app.register_blueprint(services, url_prefix='/services')
