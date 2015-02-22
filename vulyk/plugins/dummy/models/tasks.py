# -*- coding: utf-8 -*-

from vulyk.models.tasks import AbstractTask, AbstractAnswer


class DummyTask(AbstractTask):
    """
    Sample Dummy Task to work with Vulyk.
    """

    meta = {
        'collection': 'dummy_tasks',
        'allow_inheritance': True,
        'indexes': [
            'task_type'
        ]
    }


class DummyAnswer(AbstractAnswer):
    """
    Sample Dummy Answer to work with Vulyk
    """
    meta = {
        'collection': 'dummy_answers',
        'allow_inheritance': True,
        'indexes': [
            'task',
            'created_by',
            'created_at'
        ]
    }
