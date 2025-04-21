# -*- coding: utf-8 -*-
import gzip
from collections.abc import Generator
from typing import Any

import bz2file as bz2
import orjson as json
from click import echo

from vulyk.models.task_types import AbstractTaskType
from vulyk.utils import chunked


def open_anything(filename: str):
    """
    Opens a file in binary mode based on its extension.

    :param filename: Name of the file to open.
    :return: File object.
    """
    if filename.endswith(".bz2"):
        return bz2.BZ2File
    if filename.endswith(".gz"):
        return gzip.open

    return open


def load_tasks(task_type: AbstractTaskType, path: str | tuple[str], batch: str) -> int:
    """
    Loads tasks from a file into a batch.

    :param task_type: Task type to load tasks into.
    :param path: Path to load tasks from.
    :param batch: Batch ID tasks should be loaded into.

    :return: Number of tasks loaded.
    """
    if isinstance(path, str):
        path = (path,)

    count = len(path)
    tasks = 0

    for i, p in enumerate(path):
        echo("Loading file {0:d} from {1:d}...".format(i + 1, count))
        tasks += _load_tasks_file(task_type, p, batch)

    return tasks


def _load_tasks_file(task_type: AbstractTaskType, path: str, batch: str) -> int:
    """
    :param task_type: Task type to load tasks into.
    :param path: Path to load tasks from.
    :param batch: Batch ID tasks should be loaded into.

    :return: Number of stored tasks.
    """
    i = 0
    bunch_size = 100

    def _safe_load(fl) -> Generator[dict[str, Any]]:
        """
        :rtype: __generator[dict]
        """
        l = lambda s: json.loads(s) if len(s.strip()) > 0 else {}

        yield from filter(None, map(l, fl))

    try:
        with open_anything(path)(path, "rb") as f:
            for chunk in chunked(_safe_load(f), bunch_size):
                task_type.import_tasks(chunk, batch)

                i += len(chunk)
                echo("{0:d} tasks processed".format(i))
    except ValueError as e:
        echo("Error while decoding json in {0}: {1}".format(path, e))
    except IOError as e:
        echo("Got IO error when tried to decode {0}: {1}".format(path, e))

    echo("Finished loading {0:d} tasks".format(i))

    return i


def export_reports(task_id: AbstractTaskType, path: str, batch: str, *, closed: bool) -> None:
    """
    Export reports for a given task type.

    :param task_id: Task type ID to export reports for.
    :param path: Path to export reports to.
    :param batch: Batch ID to export reports for.
    :param closed: Whether to export closed tasks or not.
    """
    i = 0

    try:
        with open(path, "wb+") as f:
            for report in task_id.export_reports(batch, closed):
                f.write(json.dumps(report) + b"\n")
                i += 1

                if i + 1 % 100 == 0:
                    echo("{0:d} tasks processed".format(i))
    except ValueError as e:
        echo("Error while encoding json in {0}: {1}".format(path, e))
    except IOError as e:
        echo("Got IO error when tried to read {0}: {1}".format(path, e))

    echo("Finished exporting answers for {0:d} tasks".format(i))
