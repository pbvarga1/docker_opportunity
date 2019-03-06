from io import BytesIO

import pvl
import pytest
import aiohttp
import numpy as np

from web import pdsimage


@pytest.mark.asyncio
async def test_get_start_byte(label):
    assert await pdsimage.PDSImage._get_start_byte(label) == 195
    label['^IMAGE'] = pvl.Units(5, 'BYTES')
    assert await pdsimage.PDSImage._get_start_byte(label) == 5


@pytest.mark.asyncio
async def test_get_shape(label):
    assert await pdsimage.PDSImage._get_shape(label) == (3, 2, 4)


async def test_from_url(aiohttp_client, image):
    async def download_image(request):
        data = await image.data
        label = await image.label
        body = pvl.dumps(label) + b'\r\n' + data.tobytes()
        return aiohttp.web.Response(body=body)
    app = aiohttp.web.Application()
    url = '/image.img'
    app.router.add_get(url, download_image)
    client = await aiohttp_client(app)
    im = await pdsimage.PDSImage.from_url(url, client)
    np.testing.assert_array_equal(await im.data, await image.data)

    # Test detatched
    async def download_image(request):
        data = await image.data
        body = data.tobytes()
        return aiohttp.web.Response(body=body)

    async def download_label(request):
        label = await image.label
        body = pvl.dumps(label)
        return aiohttp.web.Response(body=body)

    image._label['^IMAGE'] = 1

    app = aiohttp.web.Application()
    app.router.add_get(url, download_image)
    app.router.add_get('/image.lbl', download_label)
    client = await aiohttp_client(app)
    im = await pdsimage.PDSImage.from_url(url, client, True)
    np.testing.assert_array_equal(await im.data, await image.data)


@pytest.mark.asyncio
async def test_product_id(image):
    assert await image.product_id == 'testimg'


@pytest.mark.asyncio
async def test_data(image):
    assert await image.data is not image._data
    np.testing.assert_array_equal(await image.data, image._data)


@pytest.mark.asyncio
async def test_label(image):
    assert await image.label is not image._label
    assert await image.label == image._label


@pytest.mark.asyncio
async def test_bands(image, gray_image):
    assert await image.bands == 3
    assert await gray_image.bands == 1


@pytest.mark.asyncio
async def test_dtype(image):
    assert str(await image.dtype) == '>i2'


@pytest.mark.asyncio
async def test_shape(image):
    assert await image.shape == (3, 2, 4)


@pytest.mark.asyncio
async def test_image(image, gray_image):
    assert (await image.image).shape == (2, 4, 3)
    assert (await gray_image.image).shape == (2, 4)


@pytest.mark.asyncio
async def test_get_png_output(image, gray_image):
    assert isinstance(await image.get_png_output(), BytesIO)
    assert b'PNG' in (await image.get_png_output()).getvalue()
    assert b'PNG' in (await gray_image.get_png_output()).getvalue()
