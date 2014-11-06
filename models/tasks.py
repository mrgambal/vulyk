# coding=utf-8
import datetime

from mongoengine import (
    StringField, IntField, DateTimeField, ListField,
    ReferenceField, DictField, CASCADE)
from flask.ext.mongoengine import Document

from .user import User


class Task(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    users_count = IntField(default=0, db_field='usersCount')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')

    title = StringField()
    text = StringField()
    structure = ListField(DictField())

    meta = {'collection': 'tasks'}

    def __unicode__(self):
        return unicode(self.id)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return unicode(self.title)


class Report(Document):
    task = ReferenceField(Task, reverse_delete_rule=CASCADE)
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE,
                                db_field="createdBy")
    created_at = DateTimeField(default=datetime.datetime.now,
                               db_field="createdAt")
    # not sure - could be extended
    found_mistakes = ListField(DictField(), db_field="foundMistakes")

    meta = {'collection': 'reports'}

    def __unicode__(self):
        return unicode(self.pk)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return u"Report [%s by %s]".format(self.created_by, self.task)
