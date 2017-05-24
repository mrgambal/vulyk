# -*- coding: utf-8 -*-
"""Every project must have a package called `utils`."""
import os
import sys
from itertools import islice

import flask
from flask import abort
import ujson as json

if sys.version_info.minor <= 4:  # PY 3.4
    import http.client as HTTPStatus
else:
    from http import HTTPStatus

__all__ = [
    'chunked',
    'get_tb',
    'get_template_path',
    'json_response',
    'NO_TASKS',
    'resolve_task_type',
    'unique'
]


# Soooo lame
def unique(source):
    """
    Returns unique values from the list preserving order of initial list.

    :param source: An iterable.
    :type source: list

    :returns: List with unique values.
    :rtype: list
    """
    seen = set()
    return [seen.add(x) or x for x in source if x not in seen]


def resolve_task_type(type_id, tasks, user):
    """
    Looks for `type_id` in TASK_TYPES map.

    :param type_id: ID of the TaskType in the map.
    :type type_id: str
    :param tasks: map of `task type id -> task type instance`
    :type tasks: dict
    :param user: Current user.
    :type user: vulyk.models.user.User

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
def chunked(iterable, n):
    """Returns chunks of n length of iterable

    If len(iterable) % n != 0, then the last chunk will have length
    less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :param iterable: Source we need to chop up.
    :type iterable: list, tuple, set
    :param n: Slice length
    :type n: int

    :returns: Sequence of tuples of given size.
    :rtype: __generator[tuple]
    """
    iterable = iter(iterable)
    while 1:
        t = tuple(islice(iterable, n))
        if t:
            yield t
        else:
            return


def get_tb():
    """
    Returns traceback of the latest exception caught in 'except' block

    :return: traceback of the most recent exception
    """
    return sys.exc_info()[2]


def get_template_path(app, name):
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


def json_response(result, template='', errors=None, status=HTTPStatus.OK):
    """
    Handy helper to prepare unified responses.

    :param result: Data to be sent
    :type result: dict
    :param template: Template name or id
    :type template: str
    :param errors: List of errors
    :type errors: list | set | tuple | dict
    :param status: Response http-status
    :type status: int

    :returns: Jsonified response
    :rtype: flask.Response
    """
    if not errors:
        errors = []

    data = json.dumps({
        'result': result,
        'template': template,
        'errors': errors})

    return flask.Response(
        data, status, mimetype='application/json',
        headers=[
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
            ('Pragma', 'no-cache'),
            ('Expires', '0'),
        ])


NO_TASKS = json_response({},
                         '',
                         ['There is no task having type like this'],
                         HTTPStatus.NOT_FOUND)
