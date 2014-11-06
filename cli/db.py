from click import echo
from slug import slug
from transliterate import translit

from app import db  # required for init db
from models import Task

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
        echo(u"Loading file {0:d} from {1:d}...".format(i, count))
        _load_tasks_file(p)


def _load_tasks_file(path):
    """
    :type path: str | basestring
    """
    i = 0
    bunch_size = 100

    if path[-4:] != "json":
        echo("Wrong file {0}".format(path))
        return

    with open(path, "rb") as f:
        for l in f:
            task = Task(**json.loads(l))
            _id = translit(task.title[0:25], "uk", reversed=True)
            task.id = slug(_id)
            task.update(upsert=True)

            i += 1

            if i % bunch_size == 0:
                echo(u"{0:d} records processed".format(i))

    echo(u"Finished loading {0:d} articles".format(i))