# -*- coding=utf-8 -*-
from __future__ import unicode_literals
import httplib
import sys
from functools import wraps
from itertools import islice

from flask import jsonify, abort


# Soooo lame
def unique(a):
    """
    Returns unique values from the list preserving order of initial list
    """
    seen = set()
    return [seen.add(x) or x for x in a if x not in seen]


def handle_exception_as_json(exc=Exception):
    if isinstance(exc, Exception):
        exc = Exception

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
                return jsonify({'result': True})
            except exc as e:
                return jsonify({'result': False, 'reason': e})

        return wrapper

    return decorator


def resolve_task_type(type_id, tasks, user):
    """
    Looks for `type_id` in TASK_TYPES list

    :type type_id: str | basestring
    :type tasks: dict
    :type user: vulyk.models.user.User

    :rtype: vulyk.models.task_types.AbstractTaskType
    """
    task_type = None

    if not (type_id and type_id in tasks.keys()):
        abort(httplib.NOT_FOUND)
    elif not user.is_eligible_for(type_id):
        abort(httplib.FORBIDDEN)
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
