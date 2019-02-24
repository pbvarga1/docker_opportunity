import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_URL = 'http://opp-app:80/api'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/product_types', methods=['POST'])
def create_product_type():
    url = f'{API_URL}/product_types'
    data = {'Name': request.json['name'].upper()}
    print(data)
    response = requests.post(url, json=data)
    response.raise_for_status()
    return jsonify(product_type=response.json())


@app.route('/product_types', methods=['GET'])
def get_product_types():
    url = f'{API_URL}/product_types'
    params = {'Active': True}
    response = requests.get(url, params=params)
    try:
        response.raise_for_status()
    except:
        return jsonify(names=[])
    product_types = response.json()
    names = [product_type['Name'] for product_type in product_types]
    return jsonify(names=names)
