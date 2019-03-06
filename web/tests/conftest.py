import time
import asyncio
from unittest.mock import patch

import pvl
import pytest
import docker
import numpy as np

from web import redis_cache, pdsimage

TEST_REDIS_PORT = 6380


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session', autouse=True)
async def redis_server_config():
    port_patch = patch('web.redis_cache.REDIS_PORT', TEST_REDIS_PORT)
    with port_patch:
        yield


@pytest.fixture(scope='session')
async def docker_container():
    client = docker.from_env()
    client.images.pull(
        repository='redis',
        tag='latest',
    )
    container = client.containers.run(
        image='redis',
        ports={'6379/tcp': f'{TEST_REDIS_PORT}'},
        detach=True,
        publish_all_ports=True,
    )
    try:
        # wait for posgres to be ready:
        n = 0
        for n, text in enumerate(container.logs(stream=True)):
            if b'Server initialized' in text:
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


@pytest.fixture
async def rcache(docker_container):
    cache = await redis_cache.get_rcache()
    await cache.flushall()
    yield cache
    await cache.flushall()


@pytest.fixture(scope='function')
async def label():
    label = pvl.PVLModule({
        'RECORD_BYTES': 3,
        '^IMAGE': 66,
        'PRODUCT_ID': 'testimg',
        'IMAGE': {
            'LINE_SAMPLES': 4,
            'LINES': 2,
            'BANDS': 3,
            'SAMPLE_TYPE': 'MSB_INTEGER',
            'SAMPLE_BITS': 16,
        },
    })
    return label


DTYPE = np.dtype('>i2')


@pytest.fixture(scope='function')
async def image(label):
    data = np.arange(1, 25).reshape((3, 2, 4))
    data = data.astype(DTYPE)
    im = pdsimage.PDSImage(data, label.copy())
    return im


@pytest.fixture(scope='function')
async def gray_image(label):
    data = np.arange(1, 9).reshape((1, 2, 4))
    data = data.astype(DTYPE)
    im = pdsimage.PDSImage(data, label.copy())
    return im
