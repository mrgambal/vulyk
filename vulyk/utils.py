# -*- coding: utf-8 -*-
"""Every project must have a package called `utils`."""
import os
import sys
from http import HTTPStatus
from itertools import islice
from typing import Iterator, Optional, Dict, Generator, Tuple

import flask
from flask import abort, Response

try:
    import ujson as json
except ImportError:
    import json

from vulyk.models.user import User

__all__ = [
    'chunked',
    'get_tb',
    'get_template_path',
    'json_response',
    'NO_TASKS',
    'resolve_task_type'
]


def resolve_task_type(type_id: str, tasks: Dict, user: User):
    """
    Looks for `type_id` in TASK_TYPES map.

    :param type_id: ID of the TaskType in the map.
    :type type_id: str
    :param tasks: map of `task type id -> task type instance`
    :type tasks: Dict[str, vulyk.models.task_types.AbstractTaskType]
    :param user: Current user.
    :type user: User

    :returns: Correct TaskType instance or throws an exception.
    :rtype: vulyk.models.task_types.AbstractTaskType
    """
    task_type = None

    if not (type_id and type_id in tasks.keys()):
        abort(HTTPStatus.NOT_FOUND)
    elif not user.is_eligible_for(type_id):
        abort(HTTPStatus.FORBIDDEN)
    else:
        task_type = tasks[type_id]

    return task_type


# Borrowed from elasticutils
def chunked(iterable: Iterator, n: int) -> Generator[Tuple, None, None]:
    """Returns chunks of n length of iterable

    If len(iterable) % n != 0, then the last chunk will have length
    less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :param iterable: Source we need to chop up.
    :type iterable: Iterator
    :param n: Slice length
    :type n: int

    :returns: Sequence of tuples of given size.
    :rtype: Generator[Tuple, None, None]
    """
    iterable = iter(iterable)

    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def get_tb() -> Dict:
    """
    Returns traceback of the latest exception caught in 'except' block

    :return: traceback of the most recent exception
    """
    return sys.exc_info()[2]


def get_template_path(app: flask.Flask, name: str) -> str:
    """
    Finds the path to the template.

    :param app: Flask application instance.
    :type app: flask.Flask
    :param name: Name of the template.
    :type name: str

    :return: Full path to the template.
    :rtype: str
    """
    for x in app.jinja_loader.list_templates():
        for folder in app.config.get('TEMPLATE_BASE_FOLDERS', []):
            if folder and os.path.join(folder, 'base', name) == x:
                return x
    return 'base/%s' % name


def json_response(result: Dict,
                  errors: Optional[Iterator] = None,
                  status: int = HTTPStatus.OK) -> Response:
    """
    Handy helper to prepare unified responses.

    :param result: Data to be sent
    :type result: Dict
    :param errors: List (set, tuple, dict) of errors
    :type errors: Optional[Iterator]
    :param status: Response http-status
    :type status: int

    :returns: Jsonified response
    :rtype: flask.Response
    """
    if not errors:
        errors = []

    data = json.dumps({
        'result': result,
        'errors': errors})

    return flask.Response(
        data, status, mimetype='application/json',
        headers=[
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
            ('Pragma', 'no-cache'),
            ('Expires', '0'),
        ])


NO_TASKS = json_response({},
                         ['There is no task having type like this'],
                         HTTPStatus.NOT_FOUND)
