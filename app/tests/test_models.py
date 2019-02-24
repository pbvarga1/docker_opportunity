from app.models import (
    Camera,
    ProductType,
    Image,
)


def test_camera_to_dict(session):
    cam = Camera(Name='foo')
    session.add(cam)
    session.commit()
    cam = Camera.query.filter().first()
    cam_dict = cam.to_dict()
    assert cam_dict['Name'] == 'foo'
    assert cam_dict['ID'] == 1
    assert cam_dict['Active']


def test_product_type_to_dict(session):
    pt = ProductType(Name='foo')
    session.add(pt)
    session.commit()
    pt = ProductType.query.filter().first()
    pt_dict = pt.to_dict()
    assert pt_dict['Name'] == 'foo'
    assert pt_dict['ID'] == 1
    assert pt_dict['Active']


def test_image_to_dict(session):
    session.add(Camera(Name='foo'))
    session.add(ProductType(Name='bar'))
    session.commit()
    session.add(Image(
        Name='foobar',
        URL='baz',
        Sol=42,
        CameraID=1,
        ProductTypeID=1,
    ))
    session.commit()
    im = Image.query.filter().first()
    im_dict = im.to_dict()
    assert im_dict['Name'] == 'foobar'
    assert im_dict['ID'] == 1
    assert im_dict['Active']
    assert im_dict['Sol'] == 42
    assert im_dict['ProductTypeID'] == 1
    assert im_dict['CameraID'] == 1
    assert im_dict['product_type']['Name'] == 'bar'
    assert im_dict['camera']['Name'] == 'foo'
