import os
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
    redis_host = os.environ.get('DOCKER_IP', '192.168.99.100')
    rcache = redis.Redis(host=redis_host, port=REDIS_PORT)
    return rcache


class HashCache(MutableMapping):

    def __init__(self, rcache: redis.Redis):
        self._rcache = rcache

    @abc.abstractproperty
    def name(self) -> str:
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

    _TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    @property
    def name(self) -> str:
        return 'image'

    def get_time(self, key: str) -> datetime:
        stamp = super().__getitem__(key).decode()
        time = datetime.strptime(stamp, self._TIME_FORMAT)
        return time

    def set_time(self, key: str) -> datetime:
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
