import os

DOCKER_HOST = os.environ.get('DOCKER_IP', '192.168.99.100')

DSN = f'http://9929242db8104494b679b60c94b0f96d@{DOCKER_HOST}:9000/2'
