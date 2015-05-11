# -*- coding: utf-8 -*-

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
    tasks = lambda: AbstractTask.objects(batch=b.id)
    f_percent = lambda done, total: (float(done) / (total or done or 1)) * 100
    a_percent = lambda got, limit, total: (float(got) / (limit * total)) * 100

    for b in Batch.objects.all():
        batches[b.id] = {
            'total': 0,
            'flag': 0,
            'flag_percent': 0,
            'answers': 0,
            'answers_percent': 0}

        if len(tasks()) > 0:
            answers = sum(tasks().scalar('users_count'))
            type_id = tasks().first().task_type
            task_type = TASKS_TYPES[type_id]

            batches[b.id] = {
                'total': b.tasks_count,
                'flag': b.tasks_processed,
                'flag_percent': f_percent(b.tasks_processed,
                                          b.tasks_count),
                'answers': answers,
                'answers_percent': a_percent(answers,
                                             task_type.redundancy,
                                             b.tasks_count)
            }

    return batches
