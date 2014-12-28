# coding=utf-8
from click import echo

from app import db

# from models.repositories import TaskRepository
import bz2
import gzip

try:
    import ujson as json
except ImportError:
    import json


def open_anything(filename):
    if filename.endswith(".bz2"):
        return bz2.BZ2File
    if filename.endswith(".gz"):
        return gzip.open

    return open


def load_tasks(task_type, path):
    """
    :type path: str | basestring
    """
    if isinstance(path, basestring):
        path = (path,)

    count = len(path)

    for i, p in enumerate(path):
        echo(u"Loading file {0:d} from {1:d}...".format(i + 1, count))
        _load_tasks_file(task_type, p)


def _load_tasks_file(task_type, path):
    """
    :type path: str | basestring
    """
    i = 0
    bunch_size = 100

    if not path.endswith(u"json"):
        echo(u"Wrong file {0}".format(path))
        return

    # repo = TaskRepository.get_instance()

    with open_anything(path)(path, "rb") as f:
        for i, l in enumerate(f):
            # repo.load_from_dict(json.loads(l))
            task_type.import_tasks([json.loads(l)])

            i += 1
            break

            if i % bunch_size == 0 and i:
                echo(u"{0:d} records processed".format(i))

    echo(u"Finished loading {0:d} articles".format(i))
