# -*- coding: utf-8 -*-
"""
Module contains all models used to keep some metadata we could use to perform
any kind of analysis.
"""
from bson import ObjectId
from mongoengine import (
    CASCADE,
    DateTimeField,
    LongField,
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
    activity = LongField()

    meta = {
        'allow_inheritance': True,
        'collection': 'work_sessions',
        'indexes': [
            ('user', 'task'),
            'task'
        ]
    }

    @classmethod
    def get_total_user_time_precise(cls, user_id: ObjectId) -> int:
        """
        Aggregated time spent doing tasks on all projects by certain user.
        As the source we use more precise value of activity field.

        :param user_id: User ID
        :type user_id: ObjectId

        :return: Total time (in seconds)
        :rtype: int
        """
        return sum(
            map(lambda session: session.activity,
                cls.objects(user=user_id)))

    @classmethod
    def get_total_user_time_approximate(cls, user_id: ObjectId) -> int:
        """
        Aggregated time spent doing tasks on all projects by certain user.
        As the source we use approximate values of start time and end time.
        Might be useful if no proper time accounting is done on frontend.

        :param user_id: User ID
        :type user_id: ObjectId

        :return: Total time (in seconds)
        :rtype: int
        """
        return sum(map(
            lambda session: (session.end_time - session.start_time).seconds,
            cls.objects(user=user_id)))
