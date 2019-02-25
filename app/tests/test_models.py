import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Camera,
    ProductType,
    Image,
)


class TestCamera:

    def test_to_dict(self, session):
        session.add(Camera(Name='foo'))
        session.commit()
        cam = Camera.query.filter().first()
        cam_dict = cam.to_dict()
        assert cam_dict['Name'] == 'foo'
        assert cam_dict['ID'] == 1
        assert cam_dict['Active']

    def test_from_dict(self):
        cam = Camera.from_dict({'Name': 'foo', 'spam': 'baz'})
        assert cam.Name == 'foo'

    def test_update_from_dict(self):
        cam = Camera(Name='foo')
        cam.update_from_dict({'Name': 'bar', 'spam': 'baz'})
        assert cam.Name == 'bar'

    def test_delete(self, session):
        session.add(Camera(Name='foo'))
        session.commit()
        cam = Camera.query.filter().first()
        assert cam.Active
        cam.delete()
        assert not cam.Active

    def test_name_is_unique(self, session):
        session.add(Camera(Name='foo'))
        session.commit()
        with pytest.raises(IntegrityError):
            session.add(Camera(Name='foo'))
            session.commit()


class TestProductType:

    def test_to_dict(self, session):
        session.add(ProductType(Name='foo'))
        session.commit()
        pt = ProductType.query.filter().first()
        pt_dict = pt.to_dict()
        assert pt_dict['Name'] == 'foo'
        assert pt_dict['ID'] == 1
        assert pt_dict['Active']

    def test_from_dict(self):
        pt = ProductType.from_dict({'Name': 'foo', 'spam': 'baz'})
        assert pt.Name == 'foo'

    def test_update_from_dict(self):
        pt = ProductType(Name='foo')
        pt.update_from_dict({'Name': 'bar', 'spam': 'baz'})
        assert pt.Name == 'bar'

    def test_delete(self, session):
        session.add(ProductType(Name='foo'))
        session.commit()
        pt = ProductType.query.filter().first()
        assert pt.Active
        pt.delete()
        assert not pt.Active

    def test_name_is_unique(self, session):
        session.add(ProductType(Name='foo'))
        session.commit()
        with pytest.raises(IntegrityError):
            session.add(ProductType(Name='foo'))
            session.commit()


@pytest.fixture(scope='function')
def image_session(session):
    """Creates a session with a camera and prod type already in the db"""
    session.add(Camera(Name='foo'))
    session.add(ProductType(Name='bar'))
    session.commit()
    return session


class TestImage:

    @pytest.fixture(scope='function', autouse=True)
    def init_image(self):
        self.image = Image(
            Name='foobar',
            URL='baz',
            Sol=42,
            CameraID=1,
            ProductTypeID=1,
            DetatchedLabel=False,
        )

    def test_to_dict(self, image_session):
        image_session.add(self.image)
        image_session.commit()
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
        assert not im_dict['DetatchedLabel']

    def test_from_dict(self):
        im = Image.from_dict(
            {
                'Name': 'foobar',
                'URL': 'baz',
                'Sol': '42',
                'CameraID': 1,
                'ProductTypeID': 1,
                'fake': 'value',
                'DetatchedLabel': True,
            }
        )
        assert im.Name == 'foobar'
        assert im.URL == 'baz'
        assert im.Sol == 42
        assert im.CameraID == 1
        assert im.ProductTypeID == 1
        assert im.DetatchedLabel

    def test_update_from_dict(self):
        self.image.update_from_dict(
            {
                'Name': 'agentp',
                'URL': 'url',
                'spam': 'baz',
                'Sol': 24,
                'CameraID': 2,
                'ProductTypeID': 3,
                'DetatchedLabel': False,
            }
        )
        assert self.image.Name == 'agentp'
        assert self.image.URL == 'url'
        assert self.image.Sol == 24
        assert self.image.CameraID == 2
        assert self.image.ProductTypeID == 3
        assert not self.image.DetatchedLabel

    def test_delete(self, image_session):
        image_session.add(self.image)
        image_session.commit()
        im = Image.query.filter().first()
        assert im.Active
        im.delete()
        assert not im.Active

    def test_name_is_unique(self, image_session):
        image_session.add(self.image)
        image_session.commit()
        im1 = Image.query.first()
        with pytest.raises(IntegrityError):
            new_im = Image.from_dict(im1.to_dict())
            image_session.add(new_im)
            image_session.commit()

    def test_many_to_one_relationships(self, image_session):
        image_session.add(self.image)
        image_session.commit()
        im1 = Image.query.first()
        # Also have the same product type id and camera id
        new_im = Image.from_dict(im1.to_dict())
        new_im.Name = 'agentp'
        image_session.add(new_im)
        image_session.commit()
        ims = Image.query.filter().all()
        assert len(ims) == 2
        im2 = ims[1]
        assert im1.ProductTypeID == 1
        assert im1.CameraID == 1
        assert im2.ProductTypeID == 1
        assert im2.CameraID == 1

        # Check the one to many relationships as well
        pt = ProductType.query.first()
        assert len(pt.images) == 2
        cam = Camera.query.first()
        assert len(cam.images) == 2
