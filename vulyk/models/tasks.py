# coding=utf-8
from datetime import datetime
from mongoengine import (
    StringField, IntField, DateTimeField, ListField, ReferenceField, DictField,
    BooleanField, CASCADE)
from flask.ext.mongoengine import Document

from . import User


class AbstractTask(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    title = StringField(max_length=200, required=True)
    task_type = StringField(max_length=50, required=True, db_field='taskType')
    users_count = IntField(default=0, db_field='usersCount')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')
    users_skipped = ListField(ReferenceField(User),
                              db_field='usersSkipped')

    task_data = DictField(required=True)

    meta = {
        'collection': 'tasks',
        'allow_inheritance': True,
        'indexes': [
            'task_type'
        ]
    }

    def as_dict(self):
        """
        Converts the model-instance into a safe and lightweight dictionary.

        :rtype : dict
        """
        return {
            "id": self.id,
            "title": self.title,
            "data": self.task_data
        }

    def __unicode__(self):
        return unicode(self.id)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return unicode(self.title)


class AbstractCloseableTask(AbstractTask):
    closed = BooleanField()

    def as_dict(self):
        d = super(AbstractCloseableTask, self).as_dict()
        d["closed"] = self.closed

        return d


class AbstractAnswer(Document):
    task = ReferenceField(AbstractTask, reverse_delete_rule=CASCADE)
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE,
                                db_field="createdBy")
    created_at = DateTimeField(default=datetime.now(),
                               db_field="createdAt")
    # not sure - could be extended
    result = DictField()

    meta = {
        'collection': 'reports',
        'allow_inheritance': True,
        'indexes': [
            'task',
            'created_by',
            'created_at'
        ]
    }

    def __unicode__(self):
        return unicode(self.pk)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return u"Report [%s by %s]".format(self.created_by, self.task)
