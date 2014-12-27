import six
import sys
from flask import jsonify, abort
from functools import wraps
from importlib import import_module


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


# Borrowed from Django project
def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


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
