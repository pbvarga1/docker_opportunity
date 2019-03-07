import os

DOCKER_HOST = os.environ.get('DOCKER_IP', '192.168.99.100')

DSN = f'http://5ea6adf6dc9c428e8e4e33474c5d2fb6@{DOCKER_HOST}:9000/3'
