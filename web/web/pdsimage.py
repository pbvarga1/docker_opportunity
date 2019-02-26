import pvl
import numpy as np

import requests


class PDSImage:

    SAMPLE_TYPES = {
        'MSB_INTEGER': '>i',
        'INTEGER': '>i',
        'MAC_INTEGER': '>i',
        'SUN_INTEGER': '>i',

        'MSB_UNSIGNED_INTEGER': '>u',
        'UNSIGNED_INTEGER': '>u',
        'MAC_UNSIGNED_INTEGER': '>u',
        'SUN_UNSIGNED_INTEGER': '>u',

        'LSB_INTEGER': '<i',
        'PC_INTEGER': '<i',
        'VAX_INTEGER': '<i',

        'LSB_UNSIGNED_INTEGER': '<u',
        'PC_UNSIGNED_INTEGER': '<u',
        'VAX_UNSIGNED_INTEGER': '<u',

        'IEEE_REAL': '>f',
        'FLOAT': '>f',
        'REAL': '>f',
        'MAC_REAL': '>f',
        'SUN_REAL': '>f',

        'IEEE_COMPLEX': '>c',
        'COMPLEX': '>c',
        'MAC_COMPLEX': '>c',
        'SUN_COMPLEX': '>c',

        'PC_REAL': '<f',
        'PC_COMPLEX': '<c',

        'MSB_BIT_STRING': '>S',
        'LSB_BIT_STRING': '<S',
        'VAX_BIT_STRING': '<S',
    }

    DTYPES = {
        '>i': 'MSB_INTEGER',
        '>u': 'MSB_UNSIGNED_INTEGER',
        '<i': 'LSB_INTEGER',
        '<u': 'LSB_UNSIGNED_INTEGER',
        '>f': 'IEEE_REAL',
        '>c': 'IEEE_COMPLEX',
        '<f': 'PC_REAL',
        '<c': 'PC_COMPLEX',
        '>S': 'MSB_BIT_STRING',
        '<S': 'LSB_BIT_STRING',
    }

    @staticmethod
    def _get_start_byte(label):
        record_bytes = label['RECORD_BYTES']
        im_pointer = label['^IMAGE']
        if isinstance(im_pointer, int):
            return (im_pointer - 1) * record_bytes

        if isinstance(im_pointer, pvl.Units) and im_pointer.units == 'BYTES':
            return im_pointer.im_pointer

    @staticmethod
    def _get_shape(label):
        samples = label['IMAGE']['LINE_SAMPLES']
        lines = label['IMAGE']['LINES']
        bands = label['IMAGE']['BANDS']
        return (bands, lines, samples)

    @classmethod
    def from_url(cls, url, detatched=False):
        resp = requests.get(url)
        resp.raise_for_status()
        content = resp.content
        if detatched:
            resp = requests.get(url.replace('.img', '.lbl'))
            resp.raise_for_status()
            lbl_content = resp.content
        else:
            lbl_content = content
        label = pvl.loads(lbl_content, strict=False)
        start_byte = cls._get_start_byte(label)
        shape = cls._get_shape(label)
        sample_type = cls.SAMPLE_TYPES[label['IMAGE']['SAMPLE_TYPE']]
        sample_byte = int(label['IMAGE']['SAMPLE_BITS'] // 8)
        dtype = np.dtype(f'{sample_type}{sample_byte}')
        data = np.frombuffer(
            buffer=content,
            dtype=dtype,
            offset=start_byte,
        )
        data = data.reshape(shape).copy()
        return cls(data, label)

    def __init__(self, data, label):
        self._label = label
        self._data = data

    @property
    def data(self):
        return self._data.copy()

    @property
    def label(self):
        return self._label.copy()

    @property
    def bands(self):
        if len(self._data.shape) == 3:
            return self._data.shape[0]
        else:
            return 1

    @property
    def image(self):
        if self.bands == 1:
            return self.data.squeeze()
        elif self.bands == 3:
            return np.dstack(self.data)
