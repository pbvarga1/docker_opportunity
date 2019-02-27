import posixpath

import requests
from flask import (
    abort,
    Flask,
    jsonify,
    request,
    make_response,
    render_template,
)

from web.pdsimage import PDSImage

app = Flask(__name__)

API_URL = 'http://opp-app:80/api'


@app.route('/')
def index():
    return render_template('index.html')


def _create_resource(resource_name, is_upper):
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


def _get_resources(resource_name):
    url = f'{API_URL}/{resource_name}'
    params = {'Active': True}
    response = requests.get(url, params=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        return jsonify(names=[])
    resources = response.json()
    return resources


@app.route('/product_types', methods=['POST'])
def create_product_type():
    product_type = _create_resource('product_types', True)
    return jsonify(product_type=product_type)


@app.route('/product_types', methods=['GET'])
def get_product_types():
    product_types = _get_resources('product_types')
    return jsonify(data=product_types)


@app.route('/cameras', methods=['POST'])
def create_camera():
    product_type = _create_resource('cameras', False)
    return jsonify(product_type=product_type)


@app.route('/cameras', methods=['GET'])
def get_cameras():
    cameras = _get_resources('cameras')
    return jsonify(data=cameras)


@app.route('/images', methods=['POST'])
def register_image():
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


@app.route('/images', methods=['GET'])
def get_images():
    params = {'Active': True}
    r = requests.get(f'{API_URL}/images', params=params)
    r.raise_for_status()
    return jsonify(data=r.json())


@app.route('/display_image', methods=['GET'])
def display_image():
    image = PDSImage.from_url(request.args['url'])
    png_output = image.get_png_output()
    response = make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response
