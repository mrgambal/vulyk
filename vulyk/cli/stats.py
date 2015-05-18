# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from vulyk.app import TASKS_TYPES
from vulyk.models.tasks import Batch, AbstractTask


def batch_completeness():
    """
    Gathers completeness stats on every batch using 2 metrics:
    - actually completed tasks
    - actual reports to total planned amount ratio (tasks * redundancy)

    :rtype : dict
    """
    batches = {}
    rs = lambda batch: AbstractTask.objects(batch=batch)
    percent = lambda done, total: (float(done) / (total or done or 1)) * 100

    for b in Batch.objects.all():
        batches[b.id] = {
            'total': 0,
            'flag': 0,
            'flag_percent': 0,
            'answers': 0,
            'answers_percent': 0,
            'breakdown': ''}

        if len(rs(b.id)) > 0:
            task_type = TASKS_TYPES[rs(b.id).first().task_type]
            answers = sum(rs(b.id).filter(closed=False).scalar('users_count'))
            answers_got = answers + (task_type.redundancy * b.tasks_processed)
            answers_needed = b.tasks_count * task_type.redundancy

            batches[b.id] = {
                'total': b.tasks_count,
                'flag': b.tasks_processed,
                'flag_percent': percent(b.tasks_processed, b.tasks_count),
                'answers': answers_got,
                'answers_percent': percent(answers_got, answers_needed),
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
