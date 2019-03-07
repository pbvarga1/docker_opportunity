import os
import re
import abc
import json
import asyncio
from datetime import datetime
from typing import Any, List, Dict, Union

import pvl
import aioredis
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


class RedisCache:
    """Base class for redis cache interface

    Parameters
    ----------
    rcache : :class:`aioredis.Redis`
        Connected redis instance
    """

    def __init__(self, rcache: aioredis.Redis):
        self._rcache = rcache


class HashCache(RedisCache):
    """Base class for redis cache interface for hashes

    Parameters
    ----------
    rcache : :class:`aioredis.Redis`
        Connected redis instance
    """

    def __repr__(self):
        items = {key: repr(value) for key, value in self.items()}
        return f'{self.__class__.__name__}({repr(items)})'

    @abc.abstractproperty
    async def name(self) -> str:
        """:obj:`str` : The name of the hash"""
        pass

    async def exists(self, key: str) -> bool:
        """Determine if a key in the hash exists

        Parameters
        ----------
        key : :obj:`str`
            The name of the key

        Returns
        -------
        exists : :obj:`bool`
            Whether or not the key exists
        """

        return await self._rcache.hexists(await self.name, key)

    async def keys(self) -> List[str]:
        """Get all the keys in the hash

        Returns
        -------
        keys : :obj:`list`[:obj:`str`]
            The keys in the hash
        """

        keys = []
        for key in await self._rcache.hkeys(await self.name):
            keys.append(key.decode())
        return keys

    async def get(self, key: str) -> Any:
        """Get the value of a key

        Parameters
        ----------
        key : :obj:`str`
            The name of the key

        Returns
        -------
        value : :obj:`bytes`
            The bytes of the value at that key
        """

        if await self.exists(key):
            return await self._rcache.hget(await self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    async def items(self) -> Dict[str, Any]:
        """Get all the items in the hash

        Returns
        -------
        items : :obj:`items`
            The items in the hash
        """

        keys = await self.keys()
        values = await asyncio.gather(*[self.get(key) for key in keys])
        items = dict(zip(keys, values))
        return items

    async def values(self) -> List[Any]:
        """Get all the values in the hash

        Returns
        -------
        values : :obj:`list`
            The values in the hash
        """

        return list((await self.items()).values())

    async def set(self, key: str, value: Any) -> Any:
        """Set a value to a key in the hash

        Parameters
        ----------
        key : :obj:`str`
            The key to set
        value : :obj:`str`
            The string value to set
        """

        if not isinstance(key, str):
            raise TypeError('key must be string')
        await self._rcache.hset(await self.name, key, value)

    async def delete(self, key: str) -> None:
        """Delete a key from the hash

        Parameters
        ----------
        key : :obj:`str`
            The name of the key
        """

        if await self.exists(key):
            await self._rcache.hdel(await self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    async def clear(self) -> None:
        """Clear all entries in the hash"""
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
        stamp = (await super().get(key)).decode()
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

    async def _set_data(self, key: str, image: PDSImage) -> None:
        data = await image.data
        await super().set(f'{key}:data', data.tobytes())

    async def _set_label(self, key: str, image: PDSImage) -> None:
        label = await image.label
        await super().set(f'{key}:label', pvl.dumps(label))

    async def _set_dtype(self, key: str, image: PDSImage) -> None:
        await super().set(f'{key}:dtype', str(await image.dtype))

    async def _set_shape(self, key: str, image: PDSImage) -> None:
        await super().set(f'{key}:shape', json.dumps(await image.shape))

    async def set(self, key: str, image: PDSImage) -> None:
        """Set an image in the hash

        The hash interface know how to properly store images so the high level
        just needs to set the image object itself

        Parameters
        ----------
        key : :obj:`str`
            The name of the image
        image : :class:`PDSImage`
            The image to cache
        """

        await asyncio.gather(
            self.set_time(key),
            self._set_data(key, image),
            self._set_label(key, image),
            self._set_dtype(key, image),
            self._set_shape(key, image),
        )

    async def get(self, key: str) -> PDSImage:
        """Get an image from the cache

        Parameters
        ----------
        key : :obj:`str`
            The name of the image
        """

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

    async def keys(self) -> List[str]:
        """Get a list of image names in the cache

        Returns
        -------
        keys : :obj:`list`[`str`]
            Names of images in the cache
        """

        keys = []
        for key in await super().keys():
            if self._INTERNAL_KEY.search(key):
                continue
            keys.append(key)
        return keys

    async def _is_internal(self, key: str) -> bool:
        if not await super().exists(key):
            return False
        if self._INTERNAL_KEY.search(key) is not None:
            return True
        else:
            return False

    async def exists(self, key: str) -> bool:
        """Determine if an image is in the cache

        Parameters
        ----------
        key : :obj:`str`
            Name of the image

        Returns
        -------
        exists : :obj:`bool`
            Whether or not the image is in the cache
        """

        if not await super().exists(key):
            return False
        elif await self._is_internal(key):
            return True
        else:
            exists = super().exists
            tasks = [exists(f'{key}:{sub}') for sub in self._SUBS]
            return all(await asyncio.gather(*tasks))


class ProgressCache(RedisCache):

    EXPIRE = 60 * 5

    async def _set(self, ID: str, progress: float, total: int,
                   size: int) -> None:
        await asyncio.gather(
            self._rcache.set(ID, str(progress), expire=self.EXPIRE),
            self._rcache.set(f'{ID}:total', str(total), expire=self.EXPIRE),
            self._rcache.set(f'{ID}:size', str(size), expire=self.EXPIRE),
        )

    async def start(self, ID: str, size: int) -> None:
        await self._set(ID, 0.0, 0, size)

    async def _exists(self, key: str) -> bool:
        return await self._rcache.exists(key)

    async def _get(self, key: str, valtype: type) -> Union[int, float]:
        value = await self._rcache.get(key)
        if value is None:
            value = '-1'
        return valtype(value)

    async def progress(self, ID: str, chunk: int) -> None:
        if self._exists(ID):
            progress: float
            total: int
            size: int
            awaitables = [
                self._get(ID, float),
                self._get(f'{ID}:total', int),
                self._get(f'{ID}:size', int),
            ]
            progress, total, size = await asyncio.gather(*awaitables)
            total += chunk
            progress = total / size
            await self._set(ID, progress, total, size)

    async def get(self, ID: str) -> float:
        return await self._get(ID, float)
