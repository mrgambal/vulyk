# -*- coding: utf-8 -*-
from bson import ObjectId
from mongoengine.base.fields import ObjectIdField

__all__ = []


# Monkey Patch for allowing queryset with unicode objects instead ObjectId
def to_python(self, value):
    if not isinstance(value, ObjectId):
        if type(value) == str:
            return value
        value = ObjectId(value)
    return value

ObjectIdField.to_python = to_python
