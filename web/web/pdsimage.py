from io import BytesIO
from typing import Tuple

import pvl
import requests
import numpy as np  # type: ignore
from matplotlib.figure import Figure  # type: ignore
from matplotlib.backends.backend_agg import (  # type: ignore
    FigureCanvasAgg as FigureCanvas,
)


class PDSImage:
    """A PDS Image that can download and display images

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        The image data
    label : :class:`pvl.PVLModule`
        The label of the image

    Examples
    --------
    >>> from web.pdsimage import PDSImage
    >>> url = (
    ...     'http://pds-geosciences.wustl.edu/mer/mer1-m-pancam-2-edr-sci-v1/'
    ...     'mer1pc_0xxx/data/sol0010/1p129069032esf0224p2812l2c1.img'
    ...)
    >>> image = PDSImage.from_url(url)
    >>> image.data.shape
    (1, 272, 361)
    >>> image.image.shape
    (272, 361)
    >>> image.label['MISSION_NAME']
    MARS EXPLORATION ROVER
    >>> image.label['PRODUCT_ID']
    1P129069032ESF0224P2812L2C1
    """

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
    def _get_start_byte(label: pvl.PVLModule) -> int:
        """Get the starting byte of the image from the label

        Parameters
        ----------
        label : :class:`pvl.PVLModule`
            The label of the image being read

        Returns
        -------
        start_byte : :obj:`int`
            The starting byte of the image in the file/contents
        """

        record_bytes = label['RECORD_BYTES']
        im_pointer = label['^IMAGE']
        if isinstance(im_pointer, int):
            return (im_pointer - 1) * record_bytes
        elif isinstance(im_pointer, pvl.Units) and im_pointer.units == 'BYTES':
            return im_pointer.value
        else:
            raise ValueError('label["^IMAGE"] should be int or pvl.Units')

    @staticmethod
    def _get_shape(label: pvl.PVLModule) -> Tuple[int, int, int]:
        """Get the shape of the image from the label

        Parameters
        ----------
        label : :class:`pvl.PVLModule`
            The label of the image being read

        Returns
        -------
        shape : :obj:`tuple` (:obj:`int`, :obj:`int`, :obj:`int`)
            The shape of the image in the file/contents
        """

        samples = label['IMAGE']['LINE_SAMPLES']
        lines = label['IMAGE']['LINES']
        bands = label['IMAGE']['BANDS']
        return (bands, lines, samples)

    @classmethod
    def from_url(cls, url: str, detatched: bool = False) -> 'PDSImage':
        """Get an image from the PDS Imaging node

        Note this does not save a local copy of the image

        Parameters
        ----------
        url : :obj:`str`
            The url to the image in the pds imaging node
        detatched : :obj:`bool`
            Whether or not the label is detatched. ``False`` by default

        Returns
        -------
        image : :class:`PDSImage`
            The image from the url
        """

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

    def __init__(self, data: np.ndarray, label: pvl.PVLModule):
        self._label = label
        self._data = data

    @property
    def data(self) -> np.ndarray:
        """:class:`numpy.ndarray` : Copy of the image's data.

        See Also
        --------
        :attr:`~PDSImage.image` : image array for viewing
        """
        return self._data.copy()

    @property
    def label(self) -> pvl.PVLModule:
        """:class:`pvl.PVLModule` : Copy of the image's label"""
        return self._label.copy()

    @property
    def bands(self) -> int:
        """:obj:`int` : The number of bands in the image"""
        if len(self._data.shape) == 3:
            return self._data.shape[0]
        else:
            return 1

    @property
    def image(self) -> np.ndarray:
        """:class:`numpy.ndarray` : data in a format for viewing"""
        if self.bands == 1:
            return self.data.squeeze()
        elif self.bands == 3:
            return np.dstack(self.data)

    def get_png_output(self) -> BytesIO:
        """Get the image as a bytes canvas for displaying on a webpage

        Returns
        -------
        :class:`io.BytesIO`
            Image as a bytes object for viewing on a webpage
        """

        fig = Figure()
        ax = fig.add_subplot(111)
        fig.patch.set_visible(False)
        cmap = 'gray' if self.bands == 1 else None
        ax.imshow(self.image, cmap=cmap)
        ax.axis('off')
        canvas = FigureCanvas(fig)
        png_output = BytesIO()
        canvas.print_png(png_output)
        return png_output
