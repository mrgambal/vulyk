# -*- coding: utf-8 -*-
"""Package contains CLI tools related to managing batches of tasks."""

from copy import deepcopy
from typing import Any

import click

from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractTask, Batch


def add_batch(
    batch_id: str, count: int, task_type: AbstractTaskType, default_batch: str, batch_meta: dict[str, Any] | None = None
) -> None:
    """
    Updates or creates new batch after loading new dataset.
    Only default batch may be extended.

    :param batch_id: Name of the batch
    :param count: Number of tasks to load
    :param task_type: Type of tasks loaded into the batch
    :param default_batch: Name of the default batch
    :param batch_meta: User params to override default batch meta

    :raise: click.BadParameter
    """
    task_type_name = task_type.type_name

    try:
        batch = Batch.objects.get(id=batch_id)

        if batch.task_type != task_type_name:
            raise click.BadParameter(
                "Batch {batch} doesn't support {task_type_name}".format(batch=batch_id, task_type_name=task_type_name)
            )
        if batch_id != default_batch:
            raise click.BadParameter("Only default batch could be extended")

        batch.update(inc__tasks_count=count)
    except Batch.DoesNotExist as err:
        meta = {}
        task_type_meta = deepcopy(task_type.task_type_meta)

        if batch_meta:
            for m_key, m_val in batch_meta.items():
                if m_key not in task_type.task_type_meta:
                    raise click.BadParameter("Meta key {} doesn't exist in task type".format(m_key)) from err  # noqa: RUF001

                try:
                    cast_to = type(task_type.task_type_meta[m_key])
                    if cast_to is not bool:
                        meta[m_key] = cast_to(m_val)
                    else:
                        meta[m_key] = m_val.lower() in ("true", "1")
                except ValueError:
                    raise click.BadParameter(
                        "Value for meta key {} cannot be converted to type {}".format(m_key, cast_to)  # noqa: RUF001
                    ) from err

            task_type_meta.update(meta)

        Batch.objects.create(id=batch_id, task_type=task_type_name, tasks_count=count, batch_meta=task_type_meta)


def validate_batch(ctx: click.Context, param: str, value: str, default_batch: str) -> str:
    """
    Refuses your attempts to add tasks to existing batch (except 'default').

    :param ctx: Click context.

    :param param: Name of parameter (`batch`).
    :param value: Value of `batch` parameter.
    :param default_batch: Name of the default batch.

    :return: the value if is valid.

    :raise: click.BadParameter
    """
    if value != default_batch and value in Batch.objects.scalar("id"):
        raise click.BadParameter("Batch with id {id} already exists".format(id=value))

    return value


def remove_batch(batch_id: str) -> None:
    """
    Delete existing batch and all tasks belonging to it.

    :param batch_id: Batch's symbolic code.

    :raise click.BadParameter: if wrong `batch_id` has been passed.
    """
    try:
        batch = Batch.objects.get(id=batch_id)
    except Batch.DoesNotExist as e:
        raise click.BadParameter("No batch was found with id " + batch_id) from e

    AbstractTask.objects(batch=batch).delete()
    batch.delete()


def batches_list() -> list[str]:
    """
    :return: List of batches IDs to validate CLI input.
    """
    return list(Batch.objects.scalar("id"))
