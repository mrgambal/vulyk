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
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
                return jsonify({"result": True})
            except Exception, e:
                return jsonify({"result": False, "reason": unicode(e)})
        return wrapper
    return decorator


def resolve_task_type(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        from app import TASKS_TYPES

        if "task_type" not in kwargs:
            abort(404)

        if kwargs["task_type"]:
            if kwargs["task_type"] not in TASKS_TYPES:
                abort(404)
            else:
                kwargs["task_type"] = TASKS_TYPES[kwargs["task_type"]]
        else:
            kwargs["task_type"] = None

        return func(*args, **kwargs)
    return decorated_view


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
