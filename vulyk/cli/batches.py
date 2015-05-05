# -*- coding: utf-8 -*-
import click

from vulyk.app import app
from vulyk.models.tasks import Batch


def add_batch(batch, count, task_type):
    """
    Updates or creates new batch after loading new dataset

    :type batch: str | unicode
    :type count: int
    :type task_type: str | unicode
    """
    if batch == app.config['DEFAULT_BATCH']:
        Batch.objects(id=batch).update_one(inc__tasks_count=count)
    else:
        Batch.objects.create(id=batch, task_type=task_type, tasks_count=count)


def validate_batch(ctx, param, value):
    """
    Refuses your attempts to add tasks to existing batch (except 'default')

    :param ctx: Click context
    :param param: Name of parameter (`batch`)
    :param value: Value of `batch` parameter

    :return: true if value passes

    :raise click.BadParameter:
    """
    if value != app.config['DEFAULT_BATCH'] and \
            value in Batch.objects.scalar('id'):
        raise click.BadParameter(
            'Batch with id {id} already exists'.format(id=value))
    else:
        return value

def batches_list():
    """
    :return: List of batches IDs to validate CLI input
    :rtype : list[str]
    """
    return Batch.objects.scalar('id')
