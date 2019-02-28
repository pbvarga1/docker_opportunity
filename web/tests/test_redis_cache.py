from datetime import datetime
from unittest.mock import patch

import redis
import pytest
import numpy as np

from web import redis_cache, pdsimage


@pytest.fixture
def image_cache(rcache):
    return redis_cache.ImageCache(rcache)


MOCK_NOW = datetime(1995, 10, 24, 7, 13, 42)


@pytest.fixture(scope='module', autouse=True)
def now():
    with patch('web.redis_cache.datetime') as mock_dt:
        mock_dt.now.return_value = MOCK_NOW
        mock_dt.strptime.side_effect = datetime.strptime
        yield


def test_get_rcache(rcache):
    assert isinstance(rcache, redis.Redis)


def test_HashCache(rcache):

    class TestCache(redis_cache.HashCache):

        @property
        def name(self):
            return 'testing'

    test_cache = TestCache(rcache)
    assert test_cache.name == 'testing'
    assert len(test_cache) == 0
    test_cache['key'] = 'value'
    assert 'key' in test_cache
    assert len(test_cache) == 1
    assert test_cache['key'] == b'value'
    assert list(iter(test_cache)) == ['key']
    assert list(test_cache.keys()) == ['key']
    test_cache['key'] = 'new'
    assert test_cache['key'] == b'new'
    del test_cache['key']
    assert 'key' not in test_cache
    with pytest.raises(KeyError):
        test_cache['key']
    with pytest.raises(KeyError):
        del test_cache['key']
    with pytest.raises(TypeError):
        test_cache[1] = 1


class TestImageCache:

    def test_name(self, image_cache):
        assert image_cache.name == 'image'

    def test_set_time(self, image_cache):
        time = image_cache.set_time('foo')
        assert time == MOCK_NOW
        assert 'foo' in image_cache
        assert redis_cache.HashCache.__getitem__(image_cache, 'foo') == (
            b'1995-10-24 07:13:42'
        )

    def test_get_time(self, image_cache):
        image_cache.set_time('foo')
        assert image_cache.get_time('foo') == MOCK_NOW

    def test__setitem__(self, image, image_cache):
        image_cache['foo'] = image
        assert 'foo' in image_cache
        assert 'foo:data' in image_cache
        assert 'foo:label' in image_cache
        assert 'foo:dtype' in image_cache
        assert 'foo:shape' in image_cache

    def test__getitem__(self, image, image_cache):
        image_cache['foo'] = image
        cached_image = image_cache['foo']
        assert isinstance(cached_image, pdsimage.PDSImage)
        np.testing.assert_array_equal(image.data, cached_image.data)
