# coding=utf-8
from mongoengine.base.fields import ObjectIdField
from bson import ObjectId

from .user import User, Group
from .tasks import AbstractTask, AbstractCloseableTask, AbstractAnswer
from .stats import EditSession


# Monkey Patch for allowing queryset with unicode objects instead ObjectId
def to_python(self, value):
    if not isinstance(value, ObjectId):
        if type(value) == unicode:
            return value
        value = ObjectId(value)
    return value

ObjectIdField.to_python = to_python
