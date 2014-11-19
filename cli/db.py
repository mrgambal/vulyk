# coding=utf-8
from click import echo

from app import db  # required for init db
from models.repositories import TaskRepository

try:
    import ujson as json
except ImportError:
    import json


def load_tasks(path):
    """
    :type path: str | basestring
    """
    if isinstance(path, basestring):
        path = (path,)

    count = len(path)

    for i, p in enumerate(path):
        echo(u"Loading file {0:d} from {1:d}...".format(i + 1, count))
        _load_tasks_file(p)


def _load_tasks_file(path):
    """
    :type path: str | basestring
    """
    i = 0
    bunch_size = 100

    if not path.endswith(u"json"):
        echo(u"Wrong file {0}".format(path))
        return

    repo = TaskRepository.get_instance()

    with open(path, "rb") as f:
        for l in f:
            repo.load_from_dict(json.loads(l))
            i += 1

            if i % bunch_size == 0:
                echo(u"{0:d} records processed".format(i))

    echo(u"Finished loading {0:d} articles".format(i))
