import os
import re
import abc
import json
import asyncio
from datetime import datetime
from typing import Generator, Any, Union

import pvl
import aioredis  # type: ignore
import numpy as np  # type: ignore

from web.pdsimage import PDSImage

REDIS_PORT = 6379


async def get_rcache() -> aioredis.Redis:
    """Get a redis object to interact with the redis cache in docker

    Returns
    -------
    rcache : :class:`redis.Redis`
        Redis interface connected to the server in docker
    """
    # Default for dockertoolbox. Set DOCKER_IP to 127.0.0.1 if not on toolbox
    redis_host = os.environ.get('DOCKER_IP', '192.168.99.100')
    address = (redis_host, REDIS_PORT)
    rcache = await aioredis.create_redis(address)
    return rcache


class HashCache:

    def __init__(self, rcache: aioredis.Redis):
        self._rcache = rcache

    def __repr__(self):
        items = {key: repr(value) for key, value in self.items()}
        return f'{self.__class__.__name__}({repr(items)})'

    @abc.abstractproperty
    async def name(self) -> str:
        """:obj:`str` : The name of the hash"""
        pass

    async def exists(self, key):
        return await self._rcache.hexists(await self.name, key)

    async def keys(self):
        keys = []
        for key in await self._rcache.hkeys(await self.name):
            keys.append(str(key))
        return keys

    async def get(self, key):
        if await self.exists(key):
            return await self._rcache.hget(await self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    async def set(self, key, value):
        if not isinstance(key, str):
            raise TypeError('key must be string')
        await self._rcache.hset(await self.name, key, value)

    async def delete(self, key):
        if await key in self:
            await self._rcache.hdel(await self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    async def clear(self):
        await self._rcache.delete(await self.name)


class ImageCache(HashCache):

    _TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    _SUBS = ['data', 'label', 'dtype', 'shape']
    _INTERNAL_KEY = re.compile(r':(data|dtype|shape|label)')

    @property
    async def name(self) -> str:
        """:obj:`str` : The name of the hash is 'image'"""
        return 'image'

    async def get_time(self, key: str) -> datetime:
        """Get the time when the image was set in the cache

        This method can be used for setting expirations on items in the cache

        Parameters
        ----------
        key : :obj:`str`
            Name of an image in the cache

        Returns
        -------
        time : :class:`datetime.datetime`
            The time the image was set in the cache
        """
        stamp = await super().get(key)
        time = datetime.strptime(stamp, self._TIME_FORMAT)
        return time

    async def set_time(self, key: str) -> datetime:
        """Update the time the for an image

        This is usefule for extending the expiration date


         Parameters
        ----------
        key : :obj:`str`
            Name of an image in the cache

        Returns
        -------
        time : :class:`datetime.datetime`
            The updated time for the image
        """

        time = datetime.now()
        await super().set(key, time.strftime(self._TIME_FORMAT))
        return time

    async def _set_data(self, key, image):
        data = await image.data
        await super().set(f'{key}:data', data.tobytes())

    async def _set_label(self, key, image):
        label = await image.label
        await super().set(f'{key}:label', pvl.dumps(label))

    async def _set_dtype(self, key, image):
        await super().set(f'{key}:dtype', str(await image.dtype))

    async def _set_shape(self, key, image):
        await super().set(f'{key}:shape', json.dumps(await image.shape))

    async def set(self, key: str, image: PDSImage) -> None:
        await asyncio.gather(
            self.set_time(key),
            self._set_data(key, image),
            self._set_label(key, image),
            self._set_dtype(key, image),
            self._set_shape(key, image),
        )

    async def get(self, key: str) -> PDSImage:
        dtype, shape, data, label = await asyncio.gather(
            super().get(f'{key}:dtype'),
            super().get(f'{key}:shape'),
            super().get(f'{key}:data'),
            super().get(f'{key}:label'),
        )
        dtype = np.dtype(dtype)
        shape = tuple(json.loads(shape))
        data = np.frombuffer(data, dtype=dtype)
        data = data.reshape(shape).copy()
        label = pvl.loads(label)
        return PDSImage(data, label)

    async def keys(self):
        keys = []
        for key in super().keys():
            if self._INTERNAL_KEY.search(key):
                continue
            keys.append(key)

    async def _is_internal(self, key):
        if not await super().exists(key):
            return False
        if self._INTERNAL_KEY.search(key) is not None:
            return True
        else:
            return False

    async def exists(self, key):
        if not await super().exists(key):
            return False
        elif await self._is_internal(key):
            return True
        else:
            exists = super().exists
            tasks = [exists(f'{key}:{sub}') for sub in self._SUBS]
            return all(await asyncio.gather(*tasks))


class LoadStatusCache(HashCache):

    @property
    async def name(self):
        return 'status'
