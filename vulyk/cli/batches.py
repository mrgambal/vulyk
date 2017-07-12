# -*- coding: utf-8 -*-
"""Package contains CLI tools related to managing batches of tasks."""

from copy import deepcopy

import click

from vulyk.models.tasks import Batch


def add_batch(batch_id, count, task_type, default_batch,
              batch_meta=None):
    """
    Updates or creates new batch after loading new dataset.
    Only default batch may be extended.

    :param batch_id: Name of the batch
    :type batch_id: str
    :param count: Number of tasks to load
    :type count: int
    :param task_type: Type of tasks loaded into the batch
    :type task_type: vulyk.models.task_types.AbstractTaskType
    :param default_batch: Name of the default batch
    :type default_batch: str
    :param batch_meta: User params to override default batch meta
    :type batch_meta: dict|None

    :raise: click.BadParameter
    """
    task_type_name = task_type.type_name
    try:
        batch = Batch.objects.get(id=batch_id)

        if batch.task_type != task_type_name:
            raise click.BadParameter(
                'Batch {batch} doesn\'t support {task_type_name}'.format(
                    batch=batch_id,
                    task_type_name=task_type_name))
        elif batch_id != default_batch:
            raise click.BadParameter(
                'Only default batch could be extended')

        batch.update(inc__tasks_count=count)
    except Batch.DoesNotExist:
        meta = {}
        task_type_meta = deepcopy(task_type.task_type_meta)

        if batch_meta:
            for m_key, m_val in batch_meta.items():
                if m_key not in task_type.task_type_meta:
                    raise click.BadParameter(
                        'Meta key {} doesn\'t exist in task type'.format(m_key)
                    )

                try:
                    cast_to = type(task_type.task_type_meta[m_key])
                    meta[m_key] = cast_to(m_val)
                except ValueError:
                    raise click.BadParameter(
                        'Value for meta key {} cannot be converted '
                        'to type {}'.format(m_key, cast_to)
                    )

            task_type_meta.update(meta)

        Batch.objects.create(
            id=batch_id,
            task_type=task_type_name,
            tasks_count=count,
            batch_meta=task_type_meta
        )


def validate_batch(ctx, param, value, default_batch):
    """
    Refuses your attempts to add tasks to existing batch (except 'default')

    :param ctx: Click context

    :param param: Name of parameter (`batch`)
    :type param: str
    :param value: Value of `batch` parameter
    :type value: str
    :param default_batch: Name of the default batch
    :type default_batch: str

    :return: true if value passes

    :raise: click.BadParameter
    """
    if value != default_batch and value in Batch.objects.scalar('id'):
        raise click.BadParameter(
            'Batch with id {id} already exists'.format(id=value))
    else:
        return value


def batches_list():
    """
    :return: List of batches IDs to validate CLI input
    :rtype: list[str]
    """
    return list(Batch.objects.scalar('id'))
