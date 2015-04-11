# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import gzip
from itertools import imap, ifilter
import os

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
    if filename.endswith('.bz2'):
        return bz2.BZ2File
    if filename.endswith('.gz'):
        return gzip.open

    return open


def load_tasks(task_id, path):
    """
    :type task_id: vulyk.models.task_types.AbstractTaskType
    :type path: str | unicode
    """
    if isinstance(path, six.string_types):
        path = (path,)

    count = len(path)

    for i, p in enumerate(path):
        echo('Loading file {0:d} from {1:d}...'.format(i + 1, count))
        _load_tasks_file(task_id, p)


def _load_tasks_file(task_id, path):
    """
    :type task_id: vulyk.models.task_types.AbstractTaskType
    :type path: str | unicode
    """
    i = 0
    bunch_size = 100

    def _safe_load(fl):
        """
        :type fl: file
        :rtype: __generator[dict]
        """
        l = lambda s: json.loads(s) if len(s.strip()) > 0 else {}

        return ifilter(None, imap(l, fl))

    try:
        with open_anything(path)(path, 'rb') as f:
            for chunk in chunked(_safe_load(f), bunch_size):
                task_id.import_tasks(chunk)

                i += len(chunk)
                echo('{0:d} tasks processed'.format(i))
    except ValueError as e:
        echo('Error while decoding json in {0}: {1}'.format(path, e))
    except IOError as e:
        echo('Got IO error when tried to decode {0}: {1}'.format(path, e))

    echo('Finished loading {0:d} tasks'.format(i))


def export_tasks(task_id, path, closed):
    """
    :type task_id: vulyk.models.task_types.AbstractTaskType
    :type path: str | unicode
    :type closed: boolean
    """
    i = 0

    try:
        with open(path, 'w+') as f:
            for report in task_id.export_reports(closed):
                f.write(json.dumps(report) + os.linesep)
                i += 1

                if i + 1 % 100 == 0:
                    echo('{0:d} tasks processed'.format(i))
    except ValueError as e:
        echo('Error while encoding json in {0}: {1}'.format(path, e))
    except IOError as e:
        echo('Got IO error when tried to decode {0}: {1}'.format(path, e))

    echo('Finished exporting answers for {0:d} tasks'.format(i))
