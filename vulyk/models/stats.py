# -*- coding: utf-8 -*-
"""
Module contains all models used to keep some metadata we could use to perform
any kind of analysis.
"""

from typing import Any, ClassVar

from bson import ObjectId
from flask_mongoengine.documents import Document
from mongoengine import CASCADE, DateTimeField, IntField, ReferenceField, StringField

from vulyk.models.tasks import AbstractAnswer, AbstractTask
from vulyk.models.user import User

__all__ = ["WorkSession"]


class WorkSession(Document):
    """
    Class which represents a timespan during which user was working on the task
    Also it stores links to every entity involved.
    """

    user = ReferenceField(User, reverse_delete_rule=CASCADE, required=True)
    task = ReferenceField(AbstractTask, reverse_delete_rule=CASCADE, required=True)
    task_type = StringField(max_length=50, required=True, db_field="taskType")
    answer = ReferenceField(AbstractAnswer, reverse_delete_rule=CASCADE)

    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=False)
    activity = IntField()

    meta: ClassVar[dict[str, Any]] = {
        "allow_inheritance": True,
        "collection": "work_sessions",
        "indexes": [("user", "task"), "task"],
    }

    @classmethod
    def get_total_user_time_precise(cls, user_id: ObjectId) -> int:
        """
        Aggregated time spent doing tasks on all projects by certain user.
        As the source we use more precise value of activity field.

        :param user_id: User ID.

        :return: Total time (in seconds).
        """
        return sum((session.activity for session in cls.objects(user=user_id)))

    @classmethod
    def get_total_user_time_approximate(cls, user_id: ObjectId) -> int:
        """
        Aggregated time spent doing tasks on all projects by certain user.
        As the source we use approximate values of start time and end time.
        Might be useful if no proper time accounting is done on frontend.

        :param user_id: User ID.

        :return: Total time (in seconds).
        """
        return sum(((session.end_time - session.start_time).seconds for session in cls.objects(user=user_id)))
