# -*- coding: utf-8 -*-
import gzip
import os

import bz2file as bz2
from click import echo

from vulyk.models.task_types import AbstractTaskType
from vulyk.utils import chunked

try:
    import ujson as json
except ImportError:
    import json


def open_anything(filename: str):
    if filename.endswith('.bz2'):
        return bz2.BZ2File
    if filename.endswith('.gz'):
        return gzip.open

    return open


def load_tasks(task_type: AbstractTaskType, path: str, batch: str) -> int:
    """

    :type task_type: AbstractTaskType
    :type path: str
    :param batch: Batch ID tasks should be loaded into
    :type batch: str

    :return: Number of tasks loaded
    :rtype: int
    """
    if isinstance(path, str):
        path = (path,)

    count = len(path)
    tasks = 0

    for i, p in enumerate(path):
        echo('Loading file {0:d} from {1:d}...'.format(i + 1, count))
        tasks += _load_tasks_file(task_type, p, batch)

    return tasks


def _load_tasks_file(task_type: AbstractTaskType, path: str, batch: str) -> int:
    """
    :type task_type: AbstractTaskType
    :type path: str
    :param batch: Batch ID tasks should be loaded into
    :type batch: str

    :return: Number of stored tasks
    :rtype: int
    """
    i = 0
    bunch_size = 100

    def _safe_load(fl):
        """
        :type fl: file
        :rtype: __generator[dict]
        """
        l = lambda s: json.loads(s) if len(s.strip()) > 0 else {}

        return filter(None, map(l, fl))

    try:
        with open_anything(path)(path, 'rb') as f:
            for chunk in chunked(_safe_load(f), bunch_size):
                task_type.import_tasks(chunk, batch)

                i += len(chunk)
                echo('{0:d} tasks processed'.format(i))
    except ValueError as e:
        echo('Error while decoding json in {0}: {1}'.format(path, e))
    except IOError as e:
        echo('Got IO error when tried to decode {0}: {1}'.format(path, e))

    echo('Finished loading {0:d} tasks'.format(i))

    return i


def export_reports(task_id: AbstractTaskType, path: str, batch: str, closed: bool) -> None:
    """
    :type task_id: AbstractTaskType
    :type path: str
    :type batch: str
    :type closed: bool
    """
    i = 0

    try:
        with open(path, 'w+') as f:
            for report in task_id.export_reports(batch, closed):
                f.write(json.dumps(report) + os.linesep)
                i += 1

                if i + 1 % 100 == 0:
                    echo('{0:d} tasks processed'.format(i))
    except ValueError as e:
        echo('Error while encoding json in {0}: {1}'.format(path, e))
    except IOError as e:
        echo('Got IO error when tried to read {0}: {1}'.format(path, e))

    echo('Finished exporting answers for {0:d} tasks'.format(i))
