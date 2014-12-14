# coding=utf-8
from datetime import datetime
from mongoengine import IntField, DateTimeField, ReferenceField, CASCADE
from flask.ext.mongoengine import Document
from models import User, Task, Report


class EditSession(Document):
    # TODO: add creation on /next and modification on /report
    user = ReferenceField(User, reverse_delete_rule=CASCADE, required=True)
    task = ReferenceField(Task, reverse_delete_rule=CASCADE, required=True)
    report = ReferenceField(Report, reverse_delete_rule=CASCADE)

    start_time = DateTimeField(required=True, default=datetime.now())
    end_time = DateTimeField(required=True, default=datetime.now())
    corrections = IntField()
