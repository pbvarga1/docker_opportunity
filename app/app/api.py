from typing import Optional, Tuple, Union, List, Callable, Any, Dict

from flask import abort, jsonify, request, Response

from app.app import (
    db,
    app,
    Base
)
from app.models import (
    Image,
    Camera,
    ProductType,
)

CodeResponse = Tuple[Response, int]


def get_data_from_json() -> dict:
    data = request.get_json()
    if data is None:
        abort(
            400,
            f'Need to pass resource information through json'
        )
    return data


def get_query_string_params() -> dict:
    params = {key: val for key, val in request.args.items()}
    return params


def get_resource(Resource: Base, ID: int) -> Union[dict, List[dict]]:
    if ID is None:
        params = get_query_string_params()
        items = [
            r.to_dict() for r in Resource.query.filter_by(**params).all()
        ]
        return items
    else:
        return Resource.query.filter_by(ID=ID).first_or_404().to_dict()


def create_resource(Resource: Base, **kwargs) -> dict:
    data = get_data_from_json()
    try:
        resource = Resource.from_dict(data)
        db.session.add(resource)
        db.session.commit()
        return resource.to_dict()
    except Exception as e:
        abort(
            400,
            f'Unable to create resource {Resource.__name__} from data '
            f'{data} with the following error: \n\n{str(e)}'
        )


def update_resource(Resource: Base, ID: Optional[int] = None,
                    **kwargs) -> dict:
    if ID is not None:
        resource = Resource.query.filter_by(ID=ID).first_or_404()
    else:
        params = get_query_string_params()
        resources = Resource.query.filter_by(**params).all()
        if not resources:
            abort(404, f'Could not find resources with params: {params}')
        elif len(resources) > 1:
            abort(
                400,
                'Too many resources, can only update one resource at a time',
            )
        else:
            resource = resources[0]
    data = get_data_from_json()
    resource.update_from_dict(data)
    db.session.add(resource)
    db.session.commit()
    return resource.to_dict()


def delete_resource(Resource: Base, ID: int) -> dict:
    if ID is None:
        abort(400, 'Delete must have an ID')
    resource = Resource.query.filter_by(ID=ID).first_or_404()
    resource.delete()
    db.session.add(resource)
    db.session.commit()

    return resource.to_dict()


@app.route(
    '/api/<string:resource>/<int:ID>',
    methods=['GET', 'PUT', 'DELETE'],
)
@app.route(
    '/api/<string:resource>',
    methods=['GET', 'POST', 'PUT', 'DELETE'],
)
def get_create_update_or_delete(resource: str,
                                ID: Optional[int] = None) -> CodeResponse:
    resources = {
        'product_types': ProductType,
        'images': Image,
        'cameras': Camera,
    }
    methods: Dict[str, Tuple[Callable[..., Any], int]]
    methods = {
        'GET': (get_resource, 200),
        'POST': (create_resource, 201),
        'DELETE': (delete_resource, 200),
        'PUT': (update_resource, 200),
    }
    Resource = resources.get(resource)
    if not Resource:
        abort(404, f'Could not find resource {resource}')

    method: Callable[..., Any]
    status_code: int
    method, status_code = methods[request.method]
    result: Union[dict, list] = method(Resource, ID=ID)
    return jsonify(result), status_code
