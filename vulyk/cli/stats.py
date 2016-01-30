# -*- coding: utf-8 -*-
from collections import OrderedDict
from mongoengine import Q

from vulyk.app import TASKS_TYPES
from vulyk.models.tasks import Batch, AbstractTask


def batch_completeness(batch_name, task_type):
    """
    Gathers completeness stats on every batch using 2 metrics:
    - actually completed tasks
    - actual reports to total planned amount ratio (tasks * redundancy)

    :param batch_name: Optional name of batch to filter by
    :type batch_name: basestring
    :param task_type: Optional name of task type to filter by
    :type task_type: basestring

    :rtype: OrderedDict
    """
    batches = OrderedDict()
    rs = lambda batch: AbstractTask.objects(batch=batch)
    percent = lambda done, total: (float(done) / (total or done or 1)) * 100
    query = Q(id=batch_name) if batch_name else Q()
    query &= Q(task_type=task_type) if task_type else Q()

    for b in Batch.objects(query).order_by('id'):
        batches[b.id] = {
            'total': 0,
            'flag': 0,
            'flag_percent': 0,
            'answers': 0,
            'answers_percent': 0,
            'breakdown': ''}

        if len(rs(b.id)) > 0:
            rs_task = TASKS_TYPES[rs(b.id).first().task_type]

            answers = rs(b.id).filter(closed=False).sum('users_count')
            answers_all = rs(b.id).sum('users_count')
            answers_mix = answers + (rs_task.redundancy * b.tasks_processed)
            answers_needed = b.tasks_count * rs_task.redundancy

            batches[b.id] = {
                'total': b.tasks_count,
                'flag': b.tasks_processed,
                'flag_percent': percent(b.tasks_processed, b.tasks_count),
                'answers': answers_all,
                'answers_percent': percent(answers_mix, answers_needed),
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
