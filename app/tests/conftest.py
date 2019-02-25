import os
import time

import pytest
import docker

from app.app import db
from app import config

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='session')
def docker_container():
    client = docker.from_env()
    # Check if image exists, build if it does not
    image, gen = client.images.build(
        path=TEST_DIR,
        tag='app-test',
        rm=True,
    )
    container = client.containers.run(
        image='app-test',
        ports={'5432': '5432'},
        detach=True,
        publish_all_ports=True,
    )
    try:
        # wait for posgres to be ready:
        n = 0
        for n, text in enumerate(container.logs(stream=True)):
            if b'database system is ready to accept connections' in text:
                time.sleep(2)
                break
            elif n < 100:
                continue

        # Posgres database ready to go
        yield container
    except Exception:
        raise
    finally:
        container.kill()
        container.remove()
        client.images.remove('app-test', force=True)


@pytest.fixture(scope='session', autouse=True)
def application():
    testing_app = db.get_app()
    testing_app.config.from_object(config.TestingConfig)
    return testing_app


@pytest.fixture
def session(application, docker_container):
    assert db.get_app().config['TESTING']
    db.session.rollback()
    db.drop_all()
    db.create_all()
    try:
        yield db.session
    except Exception:
        raise
    finally:
        # Roll back any trasactions that are in place before continuing
        db.session.rollback()
        db.drop_all()
