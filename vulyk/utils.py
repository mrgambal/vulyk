import httplib
from flask import jsonify, abort
from functools import wraps
from itertools import islice


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
                return jsonify({"result": True})
            except exc as e:
                return jsonify({"result": False, "reason": unicode(e)})
        return wrapper
    return decorator


def resolve_task_type(task_type_name):
    """
    Looks for `task_type_name` in TASK_TYPES list

    :type task_type_name: str | basestring
    :rtype: AbstractTaskType
    """
    from app import TASKS_TYPES

    task_type = None

    if task_type_name:
        if task_type_name not in TASKS_TYPES:
            abort(httplib.NOT_FOUND)
        else:
            task_type = TASKS_TYPES[task_type_name]

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
