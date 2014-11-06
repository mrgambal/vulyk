from flask import jsonify
from functools import wraps


# Soooo lame
def unique(a):
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
