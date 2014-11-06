# coding=utf-8
from models.user import *
from models.tasks import *

from mongoengine.base.fields import ObjectIdField
from bson import ObjectId


# Monkey Patch for allowing queryset with unicode objects instead ObjectId
def to_python(self, value):
    if not isinstance(value, ObjectId):
        if type(value) == unicode:
            return value
        value = ObjectId(value)
    return value

ObjectIdField.to_python = to_python
