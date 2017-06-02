# -*- coding: utf-8 -*-
"""
Module contains all models used to keep some metadata we could use to perform
any kind of analysis.
"""

from mongoengine import (
    CASCADE,
    DateTimeField,
    IntField,
    ReferenceField,
    StringField
)
from flask_mongoengine import Document

from vulyk.models.tasks import AbstractTask, AbstractAnswer
from vulyk.models.user import User

__all__ = [
    'WorkSession'
]


class WorkSession(Document):
    """
    Class which represents a timespan during which user was working on the task
    Also it stores links to every entity involved.
    """
    user = ReferenceField(User, reverse_delete_rule=CASCADE, required=True)
    task = ReferenceField(AbstractTask, reverse_delete_rule=CASCADE,
                          required=True)
    task_type = StringField(max_length=50, required=True, db_field='taskType')
    answer = ReferenceField(AbstractAnswer, reverse_delete_rule=CASCADE)

    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=False)
    activity = IntField()

    meta = {
        'collection': 'work_sessions',
        'indexes': [
            ('user', 'task'),
            'task'
        ]
    }
