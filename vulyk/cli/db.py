# -*- coding: utf-8 -*-
import gzip
from itertools import imap

from click import echo
import bz2file as bz2
import six

from vulyk.utils import chunked
from vulyk.app import db


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
    :type task_type: vulyk.models.task_types.AbstractTaskType
    :type path: str | unicode
    """
    if isinstance(path, six.string_types):
        path = (path,)

    count = len(path)

    for i, p in enumerate(path):
        echo(u"Loading file {0:d} from {1:d}...".format(i + 1, count))
        _load_tasks_file(task_type, p)


def _load_tasks_file(task_type, path):
    """
    :type task_type: vulyk.models.task_types.AbstractTaskType
    :type path: str | unicode
    """
    i = 0
    bunch_size = 100

    with open_anything(path)(path, "rb") as f:
        try:
            for chunk in chunked(imap(json.loads, f), bunch_size):
                task_type.import_tasks(chunk)

                i += len(chunk)
                echo(u"{0:d} tasks processed".format(i))
        except Exception as e:  # TODO: Except what?
            # TODO: proper error message
            echo("uhoh")
            echo(e)

    echo(u"Finished loading {0:d} tasks".format(i))
