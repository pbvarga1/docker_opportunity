import pytest
from werkzeug.exceptions import NotFound, BadRequest

from app import api
from app.models import Camera


def test_get_query_string_params(application):
    with application.test_request_context('/?foo=bar&life=42'):
        assert api.get_query_string_params() == {'foo': 'bar', 'life': '42'}


def test_get_resource_empty(session, application):
    with application.test_request_context('/api/cameras'):
        resources = api.get_resource(Camera, None)
        assert isinstance(resources, list)
        assert not resources


def test_get_resource_single_item(session):
    session.add(Camera(Name='foo'))
    session.commit()
    resource = api.get_resource(Camera, 1)
    assert isinstance(resource, dict)
    assert resource['Name'] == 'foo'
    assert resource['ID'] == 1


def test_get_resource_not_found(session):
    with pytest.raises(NotFound):
        api.get_resource(Camera, 2)


def test_get_resource_multiple_items(session, application):
    session.add(Camera(Name='foo'))
    session.commit()
    session.add(Camera(Name='bar'))
    session.commit()

    with application.test_request_context('/api/cameras/1'):
        resource = api.get_resource(Camera, 1)
        assert isinstance(resource, dict)
        assert resource['Name'] == 'foo'
        assert resource['ID'] == 1

    with application.test_request_context('/api/cameras'):
        resources = api.get_resource(Camera, None)
        assert isinstance(resources, list)
        assert resources[0]['Name'] == 'foo'
        assert resources[0]['ID'] == 1
        assert resources[1]['Name'] == 'bar'
        assert resources[1]['ID'] == 2


def test_get_data_from_json(application):
    with pytest.raises(BadRequest):
        with application.test_request_context(json=None):
            api.get_data_from_json()
    with application.test_request_context(json={'foo': 'bar'}):
        assert api.get_data_from_json() == {'foo': 'bar'}


def test_create_resource(session, application):
    # We need the session object so the item can be added to the db
    with application.test_request_context(json={'Name': 'foo'}):
        cam = api.create_resource(Camera)
    assert isinstance(cam, dict)
    assert cam['Name'] == 'foo'
    assert cam['ID'] == 1
    with pytest.raises(BadRequest):
        with application.test_request_context(json={'Name': 'foo'}):
            cam = api.create_resource(Camera)
    with pytest.raises(BadRequest):
        with application.test_request_context(json=None):
            cam = api.create_resource(Camera)


def test_update_resource(session, application):
    session.add(Camera(Name='foo'))
    session.commit()
    og_cam = Camera.query.first()

    url = "/api?Name=bar"

    with pytest.raises(NotFound):
        api.update_resource(Camera, 2)
    with pytest.raises(NotFound):
        with application.test_request_context(url):
            api.update_resource(Camera)
    with pytest.raises(BadRequest):
        with application.test_request_context(json=None):
            api.update_resource(Camera, 1)
    with application.test_request_context(json={'Name': 'bar'}):
        cam = api.update_resource(Camera, 1)
    assert cam['Name'] == 'bar'
    assert cam['Created'] == og_cam.Created.isoformat()
    assert cam['Updated'] != og_cam.Updated.isoformat()
    up1_cam = Camera.query.first()
    assert up1_cam.Name == 'bar'
    assert up1_cam.Updated.isoformat() == cam['Updated']

    with application.test_request_context(url, json={'Name': 'foo'}):
        cam = api.update_resource(Camera)
    assert cam['Name'] == 'foo'
    assert cam['Created'] == og_cam.Created.isoformat()
    assert cam['Updated'] != og_cam.Updated.isoformat()
    assert cam['Updated'] != up1_cam.Updated.isoformat()
    up2_cam = Camera.query.first()
    assert up2_cam.Name == 'foo'
    assert up2_cam.Updated.isoformat() == cam['Updated']


def test_delete_resource(session):
    session.add(Camera(Name='foo'))
    session.commit()

    og_cam = Camera.query.first()
    assert og_cam.Active

    cam = api.delete_resource(Camera, 1)
    assert not cam['Active']
    assert not Camera.query.first().Active

    with pytest.raises(BadRequest):
        api.delete_resource(Camera, None)
    with pytest.raises(NotFound):
        api.delete_resource(Camera, 2)


def test_get_create_update_or_delete(session, application):
    client = application.test_client()
    # Test create
    r = client.post('/api/cameras', json={'Name': 'foo'})
    assert r.status_code == 201
    cam1 = r.json
    r = client.post('/api/cameras', json={'Name': 'bar'})
    assert r.status_code == 201
    cam2 = r.json
    assert cam1['Name'] == 'foo'
    assert cam1['ID'] == 1
    assert cam2['Name'] == 'bar'
    assert cam2['ID'] == 2

    r = client.post('/api/product_types', json={'Name': 'EDR'})
    assert r.status_code == 201
    pt = r.json
    pt['Name'] == 'EDR'

    r = client.post(
        '/api/images',
        json={
            'Name': 'im1',
            'URL': 'url',
            'DetatchedLabel': False,
            'Sol': 42,
            'CameraID': 1,
            'ProductTypeID': 1,
        }
    )
    assert r.status_code == 201
    im = r.json
    im['Name'] == 'im1'

    # Test Update
    r = client.put('/api/cameras/2', json={'Name': 'baz'})
    assert r.status_code == 200
    assert r.json['Name'] == 'baz'

    # Test Get
    r = client.get('/api/cameras/1')
    assert r.status_code == 200
    assert r.json['Name'] == 'foo'
    r = client.get('/api/cameras')
    assert r.status_code == 200
    assert isinstance(r.json, list)
    assert len(r.json) == 2
    r = client.get('/api/cameras?Name=foo')
    assert isinstance(r.json, list)
    assert len(r.json) == 1

    # Test Delete
    r = client.delete('/api/cameras/2')
    assert r.status_code == 200
    assert not r.json['Active']
