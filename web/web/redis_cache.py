import os
import re
import abc
import json
from datetime import datetime
from collections import MutableMapping
from typing import Generator, Any, Union

import pvl
import redis  # type: ignore
import numpy as np  # type: ignore

from web.pdsimage import PDSImage

REDIS_PORT = 6379


def get_rcache() -> redis.Redis:
    """Get a redis object to interact with the redis cache in docker

    Returns
    -------
    rcache : :class:`redis.Redis`
        Redis interface connected to the server in docker
    """
    # Default for dockertoolbox. Set DOCKER_IP to 127.0.0.1 if not on toolbox
    redis_host = os.environ.get('DOCKER_IP', '192.168.99.100')
    rcache = redis.Redis(host=redis_host, port=REDIS_PORT)
    return rcache


class HashCache(MutableMapping):
    """Base class for interfacing with redis hashes

    See `redis hashes <https://redis.io/topics/data-types#hashes>`_ for more
    details on the data type. Every subclass must set a property
    :meth:`~HashCache.name` that sets the name of the hash. This interface
    allows the user to interact with redis's hashes just like python
    dictionaries.

    Parameters
    ----------
    rcache : :class:`redis.Redis`
        Redis interface connected to the server in docker. See
        :func:`get_rcache`

    Examples
    --------
    >>> from web.redis_cache import get_rcache, HashCache
    >>> class ExampleCache(HashCache):
    ...
    ...     @property
    ...     def name(self):
    ...         return 'example'
    >>> rcache = get_rcache()
    >>> example_cache = Examples(rcache)
    >>> example_cache['foo'] = 'bar'
    >>> example_cache['foo']
    b'bar'
    >>> example_cache2 = Examples(rcache)
    >>> example_cache2['foo']
    b'bar'
    """

    def __init__(self, rcache: redis.Redis):
        self._rcache = rcache

    def __repr__(self):
        items = {key: repr(value) for key, value in self.items()}
        return f'{self.__class__.__name__}({repr(items)})'

    @abc.abstractproperty
    def name(self) -> str:
        """:obj:`str` : The name of the hash"""
        pass

    def __getitem__(self, key: str) -> Union[bytes, Any]:
        if key in self:
            return self._rcache.hget(self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    def __setitem__(self, key: str, value: Any) -> None:
        if not isinstance(key, str):
            raise TypeError('key must be string')
        self._rcache.hset(self.name, key, value)

    def __delitem__(self, key: str) -> None:
        if key in self:
            self._rcache.hdel(self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    def __iter__(self) -> Generator[str, None, None]:
        for key in self._rcache.hkeys(self.name):
            yield key.decode()

    def __len__(self) -> int:
        return self._rcache.hlen(self.name)

    def __contains__(self, key: Any) -> bool:
        return self._rcache.hexists(self.name, key)


class ImageCache(HashCache):
    """Cache PDSImages so the user does not have to redownload to display again

    This interface allows the users to cache :class:`~web.pdsimage.PDSImage`
    objects directly and should be indexed by the key. Then getting the image
    objects is as simple as using the image name as the key. Each cached image
    is stored with a datetime

    Parameters
    ----------
    rcache : :class:`redis.Redis`
        Redis interface connected to the server in docker. See
        :func:`get_rcache`

    Examples
    --------
    >>> from web.pdsimage import PDSImage
    >>> from web.redis_cache import get_rcache, ImageCache
    >>> url = (
    ...     'http://pds-geosciences.wustl.edu/mer/mer1-m-pancam-2-edr-sci-v1/'
    ...     'mer1pc_0xxx/data/sol0010/1p129069032esf0224p2812l2c1.img'
    ...)
    >>> image = PDSImage.from_url(url)
    >>> image.image[:3, :3]
    array([[1566, 1586, 1586],
       [1586, 1606, 1606],
       [1586, 1606, 1647]], dtype=int16)
    >>> image.label['PRODUCT_ID']
    1P129069032ESF0224P2812L2C1
    >>> rcache = get_rcache()
    >>> image_cache = ImageCache(rcache)
    >>> image_cache['1p129069032esf0224p2812l2c1.img'] = image
    >>> cached_image = image_cache['1p129069032esf0224p2812l2c1.img']
    >>> cached_image.image[:3, :3]
    array([[1566, 1586, 1586],
       [1586, 1606, 1606],
       [1586, 1606, 1647]], dtype=int16)
    >>> cached_image.label['PRODUCT_ID']
    1P129069032ESF0224P2812L2C1
    >>> list(image_cache.keys())
    ['1p129069032esf0224p2812l2c1.img']
    >>> image_cache.get_time('1p129069032esf0224p2812l2c1.img')
    datetime.datetime(2019, 2, 28, 18, 54, 27)
    >>> image_cache.set_time('1p129069032esf0224p2812l2c1.img')
    datetime.datetime(2019, 2, 28, 18, 54, 28)
    >>> image_cache.get_time('1p129069032esf0224p2812l2c1.img')
    datetime.datetime(2019, 2, 28, 18, 54, 28)
    """

    _TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    @property
    def name(self) -> str:
        """:obj:`str` : The name of the hash is 'image'"""
        return 'image'

    def get_time(self, key: str) -> datetime:
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
        stamp = super().__getitem__(key).decode()
        time = datetime.strptime(stamp, self._TIME_FORMAT)
        return time

    def set_time(self, key: str) -> datetime:
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
        super().__setitem__(key, time.strftime(self._TIME_FORMAT))
        return time

    def __setitem__(self, key: str, image: PDSImage) -> None:
        self.set_time(key)
        super().__setitem__(f'{key}:data', image.data.tobytes())
        super().__setitem__(f'{key}:label', pvl.dumps(image.label))
        super().__setitem__(f'{key}:dtype', str(image.data.dtype))
        super().__setitem__(f'{key}:shape', json.dumps(image.data.shape))

    def __getitem__(self, key: str) -> PDSImage:
        dtype = np.dtype(super().__getitem__(f'{key}:dtype'))
        shape = tuple(json.loads(super().__getitem__(f'{key}:shape')))
        data = np.frombuffer(super().__getitem__(f'{key}:data'), dtype=dtype)
        data = data.reshape(shape).copy()
        label = pvl.loads(super().__getitem__(f'{key}:label'))
        return PDSImage(data, label)

    def __iter__(self):
        internal_key = re.compile(r':(data|dtype|shape|label)')
        for key in super().__iter__():
            if internal_key.search(key):
                continue
            yield key
