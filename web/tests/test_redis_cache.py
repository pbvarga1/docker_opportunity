from datetime import datetime
from unittest.mock import patch

import aioredis
import pytest
import numpy as np

from web import redis_cache, pdsimage


@pytest.fixture
async def image_cache(rcache):
    return redis_cache.ImageCache(rcache)


MOCK_NOW = datetime(1995, 10, 24, 7, 13, 42)


@pytest.fixture(scope='module', autouse=True)
async def now():
    with patch('web.redis_cache.datetime') as mock_dt:
        mock_dt.now.return_value = MOCK_NOW
        mock_dt.strptime.side_effect = datetime.strptime
        yield


@pytest.mark.asyncio
async def test_get_rcache(rcache):
    assert isinstance(rcache, aioredis.Redis)


@pytest.mark.asyncio
async def test_HashCache(rcache):

    class TestCache(redis_cache.HashCache):

        @property
        async def name(self):
            return 'testing'

    test_cache = TestCache(rcache)
    assert await test_cache.name == 'testing'
    assert not await test_cache.exists('foo')
    await test_cache.set('foo', 'bar')
    assert await test_cache.exists('foo')
    assert await test_cache.get('foo') == b'bar'
    await test_cache.set('baz', 'spam')
    await test_cache.set('life', '42')
    assert await test_cache.items() == {
        'foo': b'bar',
        'baz': b'spam',
        'life': b'42',
    }
    assert await test_cache.values() == [b'bar', b'spam', b'42']
    assert await test_cache.exists('baz')
    assert await test_cache.exists('life')
    assert sorted(await test_cache.keys()) == ['baz', 'foo', 'life']
    await test_cache.delete('foo')
    assert not await test_cache.exists('foo')
    assert await test_cache.exists('baz')
    assert await test_cache.exists('life')
    await test_cache.clear()
    assert not await test_cache.exists('baz')
    assert not await test_cache.exists('life')


class TestImageCache:

    @pytest.mark.asyncio
    async def test_name(self, image_cache):
        assert await image_cache.name == 'image'

    @pytest.mark.asyncio
    async def test_get_time(self, image, image_cache):
        await image_cache.set('foo', image)
        await image_cache.set_time('foo')
        assert await image_cache.get_time('foo') == MOCK_NOW

    @pytest.mark.asyncio
    async def test_set_time(self, rcache, image_cache):
        time = await image_cache.set_time('foo')
        assert time == MOCK_NOW
        assert await redis_cache.HashCache.exists(image_cache, 'foo')

        class MockImageCache(redis_cache.HashCache):

            @property
            async def name(self):
                return 'image'

        mock_image_cache = MockImageCache(rcache)
        assert await mock_image_cache.get('foo') == (
            b'1995-10-24 07:13:42'
        )

    @pytest.mark.asyncio
    async def test_set_data(self, image, image_cache):
        await image_cache._set_data('foo', image)
        assert await image_cache.exists('foo:data')

    @pytest.mark.asyncio
    async def test_set_label(self, image, image_cache):
        await image_cache._set_label('foo', image)
        assert await image_cache.exists('foo:label')

    @pytest.mark.asyncio
    async def test_set_dtype(self, image, image_cache):
        await image_cache._set_dtype('foo', image)
        assert await image_cache.exists('foo:dtype')

    @pytest.mark.asyncio
    async def test_set_shape(self, image, image_cache):
        await image_cache._set_shape('foo', image)
        assert await image_cache.exists('foo:shape')

    @pytest.mark.asyncio
    async def test_set(self, image, image_cache):
        await image_cache.set('foo', image)
        assert await image_cache.exists('foo')
        assert await image_cache.exists('foo:data')
        assert await image_cache.exists('foo:label')
        assert await image_cache.exists('foo:dtype')
        assert await image_cache.exists('foo:shape')

    @pytest.mark.asyncio
    async def test_get(self, image, image_cache):
        await image_cache.set('foo', image)
        cached_image = await image_cache.get('foo')
        assert isinstance(cached_image, pdsimage.PDSImage)
        np.testing.assert_array_equal(
            await image.data,
            await cached_image.data,
        )

    @pytest.mark.asyncio
    async def test_keys(self, image, gray_image, image_cache):
        await image_cache.set('foo', image)
        await image_cache.set('bar', gray_image)
        expected_keys = ['bar', 'foo']
        assert list(sorted(await image_cache.keys())) == expected_keys

    @pytest.mark.asyncio
    async def test_is_internal(self, image, gray_image, image_cache):
        await image_cache.set('foo', image)
        assert not await image_cache._is_internal('foo')
        assert not await image_cache._is_internal('bar')
        assert await image_cache._is_internal('foo:data')
        assert await image_cache._is_internal('foo:dtype')
        assert await image_cache._is_internal('foo:label')
        assert await image_cache._is_internal('foo:shape')

    @pytest.mark.asyncio
    async def test_exists(self, image, gray_image, image_cache):
        await image_cache.set('foo', image)
        assert await image_cache.exists('foo')
        assert await image_cache.exists('foo:data')
        assert await image_cache.exists('foo:dtype')
        assert await image_cache.exists('foo:label')
        assert await image_cache.exists('foo:shape')
        # Set item without internal entries
        await redis_cache.HashCache.set(image_cache, 'bar', 'baz')
        assert await redis_cache.HashCache.exists(image_cache, 'bar')
        assert not await image_cache.exists('bar')
