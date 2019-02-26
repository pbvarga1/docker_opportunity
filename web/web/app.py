import requests
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)

API_URL = 'http://opp-app:80/api'


@app.route('/')
def index():
    return render_template('index.html')


def _create_resource(resource_name):
    url = f'{API_URL}/{resource_name}'
    try:
        data = {'Name': request.json['name'].upper()}
    except KeyError:
        abort(400, 'json format should be {"name": "<value>"')
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()


def _get_resources_names(resource_name):
    url = f'{API_URL}/{resource_name}'
    params = {'Active': True}
    response = requests.get(url, params=params)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        return jsonify(names=[])
    resources = response.json()
    names = [resource['Name'] for resource in resources]
    return names


@app.route('/product_types', methods=['POST'])
def create_product_type():
    product_type = _create_resource('product_types')
    return jsonify(product_type=product_type)


@app.route('/product_types', methods=['GET'])
def get_product_types():
    names = _get_resources_names('product_types')
    print(names)
    return jsonify(names=names)


@app.route('/cameras', methods=['POST'])
def create_camera():
    product_type = _create_resource('cameras')
    return jsonify(product_type=product_type)


@app.route('/cameras', methods=['GET'])
def get_cameras():
    names = _get_resources_names('cameras')
    return jsonify(names=names)
