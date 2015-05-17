# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from vulyk.app import TASKS_TYPES
from vulyk.models.tasks import Batch, AbstractTask, AbstractAnswer


def batch_completeness():
    """
    Gathers completeness stats on every batch using 2 metrics:
    - actually completed tasks
    - actual reports to total planned amount ratio (tasks * redundancy)

    :rtype : dict
    """
    batches = {}
    tasks = lambda batch: AbstractTask.objects(batch=batch)
    percent = lambda done, total: (float(done) / (total or done or 1)) * 100

    for b in Batch.objects.all():
        batches[b.id] = {
            'total': 0,
            'flag': 0,
            'flag_percent': 0,
            'answers': 0,
            'answers_percent': 0,
            'breakdown': ''}

        if len(tasks(b.id)) > 0:
            type_id = tasks(b.id).first().task_type
            task_type = TASKS_TYPES[type_id]
            answers = sum(tasks(b.id).filter(closed=False).scalar('users_count'))
            done = answers + (task_type.redundancy * b.tasks_processed)

            batches[b.id] = {
                'total': b.tasks_count,
                'flag': b.tasks_processed,
                'flag_percent': percent(b.tasks_processed, b.tasks_count),
                'answers': done,
                'answers_percent': percent(done, b.tasks_count),
                'breakdown': _breakdown_by_processed(b.id)
            }

    return batches


def _breakdown_by_processed(batch):
    """
    Combines stats on responses count ratio for certain batch

    :param batch: Batch ID
    :type batch: str | basestring

    :returns: string ready to be displayed in CLI
    :rtype: str
    """
    result = []
    rs = AbstractTask.objects(batch=batch)

    for i in rs.item_frequencies('users_count').items():
        result.append('{:>12}: {}'.format(*i))

    return '\n'.join(result)
