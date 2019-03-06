import asyncio
from io import BytesIO
from typing import Tuple, Union

import pvl
import aiohttp
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
    >>> image.image[:3, :3]
    array([[1566, 1586, 1586],
       [1586, 1606, 1606],
       [1586, 1606, 1647]], dtype=int16)
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
    async def _get_start_byte(label: pvl.PVLModule) -> int:
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
    async def _get_shape(label: pvl.PVLModule) -> Tuple[int, int, int]:
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
    async def from_url(cls, url: str, session: aiohttp.ClientSession,
                       detached: bool = False) -> 'PDSImage':
        """Get an image from the PDS Imaging node

        Note this does not save a local copy of the image

        Parameters
        ----------
        url : :obj:`str`
            The url to the image in the pds imaging node
        session : :class:`aiohttp.ClientSession`
            Open client session for making requests asynchronously
        detached : :obj:`bool`
            Whether or not the label is detached. ``False`` by default

        Returns
        -------
        image : :class:`PDSImage`
            The image from the url
        """

        async with session.get(url) as resp:
            content = await resp.read()
        if detached:
            async with session.get(url.replace('.img', '.lbl')) as resp:
                lbl_content = await resp.read()
        else:
            lbl_content = content
        label = pvl.loads(lbl_content, strict=False)
        start_byte_fut = cls._get_start_byte(label)
        shape_fut = cls._get_shape(label)
        sample_type = cls.SAMPLE_TYPES[label['IMAGE']['SAMPLE_TYPE']]
        sample_byte = int(label['IMAGE']['SAMPLE_BITS'] // 8)
        dtype = np.dtype(f'{sample_type}{sample_byte}')
        data = np.frombuffer(
            buffer=content,
            dtype=dtype,
            offset=await start_byte_fut,
        )
        data = data.reshape(await shape_fut).copy()
        return cls(data, label)

    def __init__(self, data: np.ndarray, label: pvl.PVLModule):
        self._label = label
        self._data = data

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._label["PRODUCT_ID"]})'

    @property
    async def product_id(self) -> str:
        """:obj:`str` : The product ID from the label"""
        return self._label['PRODUCT_ID']

    @property
    async def data(self) -> np.ndarray:
        """:class:`numpy.ndarray` : Copy of the image's data.

        See Also
        --------
        :attr:`~PDSImage.image` : image array for viewing
        """
        return self._data.copy()

    @property
    async def label(self) -> pvl.PVLModule:
        """:class:`pvl.PVLModule` : Copy of the image's label"""
        return self._label.copy()

    @property
    async def bands(self) -> int:
        """:obj:`int` : The number of bands in the image"""
        if len(self._data.shape) == 3:
            return self._data.shape[0]
        else:
            return 1

    @property
    async def dtype(self) -> np.dtype:
        """:class:`numpy.dtype` : The data's dtype"""
        return self._data.dtype

    @property
    async def shape(self) -> Union[Tuple[int, int, int], Tuple[int, int]]:
        """":obj:`tuple` : The data's shape"""
        return self._data.shape

    @property
    async def image(self) -> np.ndarray:
        """:class:`numpy.ndarray` : data in a format for viewing"""
        data, bands = await asyncio.gather(self.data, self.bands)

        if bands == 1:
            return data.squeeze()
        elif bands == 3:
            return np.dstack(data)

    async def get_png_output(self) -> BytesIO:
        """Get the image as a bytes canvas for displaying on a webpage

        Returns
        -------
        :class:`io.BytesIO`
            Image as a bytes object for viewing on a webpage
        """

        fig = Figure()
        ax = fig.add_subplot(111)
        fig.patch.set_visible(False)
        cmap = 'gray' if await self.bands == 1 else None
        ax.imshow(await self.image, cmap=cmap)
        ax.axis('off')
        canvas = FigureCanvas(fig)
        png_output = BytesIO()
        canvas.print_png(png_output)
        return png_output
