from sqlalchemy.sql.expression import true
from flask import abort, jsonify, request, Response

from app.app import (
    db,
    app,
)
from app.models import (
    Image,
    Camera,
    ProductType,
)


@app.route(
    '/api/<string:resource>/<int:ID>',
    methods=['GET', 'POST', 'UPDATE', 'DELETE'],
)
@app.route(
    '/api/<string:resource>',
    methods=['GET', 'POST', 'UPDATE', 'DELETE'],
)
def get_create_update_or_delete(resource, ID=None):
    resources = {
        'product_types': ProductType,
        'images': Image,
        'cameras': Camera,
    }
    methods = {
        'GET': get_resource,
        'POST': create_resource,
        'DELETE': delete_resource,
        'UPDATE': update_resource,
    }
    Resource = resources.get(resource)
    if not Resource:
        abort(Response(f'Could not find resource {resource}'), 404)

    method = methods[request.method]
    return jsonify(method(Resource, ID=ID))


def get_resource(Resource, ID):
    if ID is None:
        items = [
            r.to_dict() for r in Resource.query.filter_by(Active=true()).all()
        ]
        return items
    else:
        return Resource.query.filter_by(ID=ID).first_or_404().to_dict()


def create_resource(Resource, **kwargs):
    resource = Resource.from_dict(request.get_json())
    db.session.add(resource)
    db.session.commit()
    return resource.to_dict()


def update_resource(Resource, ID=None, **kwargs):
    if ID is not None:
        resource = Resource.query.filter_by(ID=ID).first_or_404()
    else:
        resources = Resource.query.filter_by(**request.args).all()
        if not resources:
            abort(404)
        elif len(resources) > 1:
            abort(400)
        else:
            resource = resources[0]
    resource.update_from_dict(request.get_json())
    db.session.add(resource)
    db.session.commit()
    return resource.to_dict()


def delete_resource(Resource, ID):
    if ID is None:
        abort(Response('Delete must have an ID', 404))
    resource = Resource.query.filter_by(ID=ID).first_or_404()
    resource.delete()
    db.session.add(resource)
    db.session.commit()
