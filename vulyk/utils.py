# -*- coding: utf-8 -*-
"""Every project must have a package called `utils`."""

import os
from collections.abc import Generator, Iterable
from http import HTTPStatus
from itertools import islice
from typing import Any

import flask
import orjson as json
from flask import Response, abort

from vulyk.models.task_types import AbstractTaskType
from vulyk.models.user import User

__all__ = ["NO_TASKS", "chunked", "get_template_path", "json_response", "resolve_task_type"]


def resolve_task_type(type_id: str, tasks: dict[str, AbstractTaskType], user: User) -> AbstractTaskType:
    """
    Looks for `type_id` in TASK_TYPES map.

    :param type_id: ID of the TaskType in the map.
    :param tasks: map of `task type id -> task type instance`
    :param user: Current user.

    :returns: Correct TaskType instance or throws an exception.
    """
    task_type = None

    if not (type_id and type_id in tasks):
        abort(HTTPStatus.NOT_FOUND)
    elif not user.is_eligible_for(type_id):
        abort(HTTPStatus.FORBIDDEN)
    else:
        task_type = tasks[type_id]

    return task_type


# Borrowed from elasticutils
def chunked(iterable: Iterable, n: int) -> Generator[tuple]:
    """Returns chunks of n length of iterable.

    If len(iterable) % n != 0, then the last chunk will have length
    less than n.

    Example:

    >>> chunked([1, 2, 3, 4, 5], 2)
    [(1, 2), (3, 4), (5,)]

    :param iterable: Source we need to chop up.
    :param n: Slice length.

    :returns: Sequence of tuples of given size.
    """
    iterable = iter(iterable)

    while 1:
        if t := tuple(islice(iterable, n)):
            yield t
        else:
            return


def get_template_path(app: flask.Flask, name: str) -> str:
    """
    Finds the path to the template.

    :param app: Flask application instance.
    :param name: Name of the template.

    :return: Full path to the template.
    """
    for x in app.jinja_loader.list_templates():
        for folder in app.config.get("TEMPLATE_BASE_FOLDERS", []):
            if folder and os.path.join(folder, "base", name) == x:
                return x
    return "base/%s" % name


def json_response(result: dict[str, Any], errors: Iterable[Any] | None = None, status: int = HTTPStatus.OK) -> Response:
    """
    Handy helper to prepare unified responses.

    :param result: Data to be sent.
    :param errors: Sequence of errors.
    :param status: Response http-status.

    :returns: Jsonified response.
    """
    if not errors:
        errors = []

    data = json.dumps({"result": result, "errors": errors})

    return flask.Response(
        data,
        status,
        mimetype="application/json",
        headers=[
            ("Cache-Control", "no-cache, no-store, must-revalidate"),
            ("Pragma", "no-cache"),
            ("Expires", "0"),
        ],
    )


NO_TASKS = json_response({}, ["There is no task having type like this"], HTTPStatus.NOT_FOUND)
