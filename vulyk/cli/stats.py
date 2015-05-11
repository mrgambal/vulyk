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
    tasks = lambda batch: AbstractTask.objects(batch=batch.id)
    percent = lambda done, total: (float(done) / (total or done or 1)) * 100

    for b in Batch.objects.all():
        batches[b.id] = {
            'total': 0,
            'flag': 0,
            'flag_percent': 0,
            'answers': 0,
            'answers_percent': 0}

        if len(tasks(b)) > 0:
            type_id = tasks(b).first().task_type
            task_type = TASKS_TYPES[type_id]
            answers = sum(tasks(b).filter(closed=False).scalar('users_count'))
            done = answers + (task_type.redundancy * b.tasks_processed)

            batches[b.id] = {
                'total': b.tasks_count,
                'flag': b.tasks_processed,
                'flag_percent': percent(b.tasks_processed, b.tasks_count),
                'answers': done,
                'answers_percent': percent(done, b.tasks_count)
            }

    return batches
