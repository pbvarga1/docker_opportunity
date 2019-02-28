import abc
import json
from datetime import datetime
from collections import MutableMapping

import pvl
import redis
import numpy as np

from web.pdsimage import PDSImage

REDIS_PORT = 6379
REDIS_HOST = '192.168.99.100'


def get_rcache():
    rcache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    return rcache


class HashCache(MutableMapping):

    def __init__(self, rcache):
        self._rcache = rcache

    @abc.abstractproperty
    def name(self):
        pass

    def __getitem__(self, key):
        if key in self:
            return self._rcache.hget(self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError('key must be string')
        self._rcache.hset(self.name, key, value)

    def __delitem__(self, key):
        if key in self:
            self._rcache.hdel(self.name, key)
        else:
            raise KeyError(f'{repr(key)}')

    def __iter__(self):
        for key in self._rcache.hkeys(self.name):
            yield key.decode()

    def __len__(self):
        return self._rcache.hlen(self.name)

    def __contains__(self, key):
        return self._rcache.hexists(self.name, key)


class ImageCache(HashCache):

    _TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    @property
    def name(self):
        return 'image'

    def get_time(self, key):
        stamp = super().__getitem__(key).decode()
        time = datetime.strptime(stamp, self._TIME_FORMAT)
        return time

    def set_time(self, key):
        time = datetime.now()
        super().__setitem__(key, time.strftime(self._TIME_FORMAT))
        return time

    def __setitem__(self, key, image):
        self.set_time(key)
        super().__setitem__(f'{key}:data', image.data.tobytes())
        super().__setitem__(f'{key}:label', pvl.dumps(image.label))
        super().__setitem__(f'{key}:dtype', str(image.data.dtype))
        super().__setitem__(f'{key}:shape', json.dumps(image.data.shape))

    def __getitem__(self, key):
        dtype = np.dtype(super().__getitem__(f'{key}:dtype'))
        shape = tuple(json.loads(super().__getitem__(f'{key}:shape')))
        data = np.frombuffer(super().__getitem__(f'{key}:data'), dtype=dtype)
        data = data.reshape(shape).copy()
        label = pvl.loads(super().__getitem__(f'{key}:label'))
        return PDSImage(data, label)
