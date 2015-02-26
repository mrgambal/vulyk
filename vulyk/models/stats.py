# -*- coding=utf-8 -*-

from datetime import datetime
from mongoengine import IntField, DateTimeField, ReferenceField, CASCADE
from flask.ext.mongoengine import Document

from vulyk.models.tasks import AbstractTask, AbstractAnswer
from vulyk.models.user import User


class WorkSession(Document):
    user = ReferenceField(User, reverse_delete_rule=CASCADE, required=True)
    task = ReferenceField(AbstractTask, reverse_delete_rule=CASCADE,
                          required=True)
    answer = ReferenceField(AbstractAnswer, reverse_delete_rule=CASCADE)

    start_time = DateTimeField(required=True, default=datetime.now())
    end_time = DateTimeField(required=True)
    corrections = IntField()

    meta = {
        'collection': 'work_sessions',
        'indexes': [
            ('user', 'task'),
            'task'
        ]
    }
