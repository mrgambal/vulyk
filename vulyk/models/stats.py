# -*- coding: utf-8 -*-
"""
Module contains all models used to keep some metadata we could use to perform
any kind of analysis.
"""

from datetime import datetime

from mongoengine import IntField, DateTimeField, ReferenceField, CASCADE
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
    answer = ReferenceField(AbstractAnswer, reverse_delete_rule=CASCADE)

    start_time = DateTimeField(required=True, default=datetime.now())
    end_time = DateTimeField(required=False)
    corrections = IntField()

    meta = {
        'collection': 'work_sessions',
        'indexes': [
            ('user', 'task'),
            'task'
        ]
    }
