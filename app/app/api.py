import logging
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

logger = logging.getLogger(__name__)


def get_data_from_json() -> dict:
    data = request.get_json()
    if data is None:
        msg = 'Need to pass resource information through json'
        logging.error(msg)
        abort(400, msg)
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
    logger.info(f'Creating Resource: {type(Resource).__name__}')
    data = get_data_from_json()
    try:
        resource = Resource.from_dict(data)
        db.session.add(resource)
        db.session.commit()
        logger.info('Success')
        return resource.to_dict()
    except Exception as e:
        logger.exception(
            f'Failed to create eesource: {type(Resource).__name__}'
        )
        abort(
            400,
            f'Unable to create resource {Resource.__name__} from data '
            f'{data} with the following error: \n\n{str(e)}'
        )


def update_resource(Resource: Base, ID: Optional[int] = None,
                    **kwargs) -> dict:
    if ID is not None:
        resource = Resource.query.filter_by(ID=ID).first_or_404()
        logger.info(
            f'Updating resource {type(Resource).__name__} with ID {ID}'
        )
    else:
        params = get_query_string_params()
        resources = Resource.query.filter_by(**params).all()
        if not resources:
            msg = (
                f'Could not find resource {type(Resource).__name__} '
                f'with params: {params}'
            )
            logger.error(msg)
            abort(404, msg)
        elif len(resources) > 1:
            msg = (
                f'Found too many resources {type(Resource).__name__} '
                f'with params: {params}'
            )
            logger.error(msg)
            abort(400, msg)
        else:
            resource = resources[0]
            logger.info(
                f'Updating resource {type(Resource).__name__} with '
                f'ID {resource["ID"]}'
            )
    data = get_data_from_json()
    resource.update_from_dict(data)
    db.session.add(resource)
    db.session.commit()
    logger.info('Success')
    return resource.to_dict()


def delete_resource(Resource: Base, ID: int) -> dict:
    if ID is None:
        msg = 'Delete must have an ID'
        logger.error(msg)
        abort(400, msg)
    logger.info(f'Deleting resource {type(Resource).__name__} with ID {ID}')
    resource = Resource.query.filter_by(ID=ID).first_or_404()
    resource.delete()
    db.session.add(resource)
    db.session.commit()
    logger.info('Success')

    return resource.to_dict()


@app.route(
    '/api/<string:resource>/<int:ID>',
    methods=['GET', 'PUT', 'DELETE'],
)
@app.route(
    '/api/<string:resource>',
    methods=['GET', 'POST'],
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
