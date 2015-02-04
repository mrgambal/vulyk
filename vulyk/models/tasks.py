# coding=utf-8
from datetime import datetime
from mongoengine import (
    StringField, IntField, DateTimeField, ListField, ReferenceField, DictField,
    BooleanField, CASCADE)
from flask.ext.mongoengine import Document

from vulyk.models import User


class AbstractTask(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    task_type = StringField(max_length=50, required=True, db_field='taskType')

    users_count = IntField(default=0, db_field='usersCount')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')
    users_skipped = ListField(ReferenceField(User),
                              db_field='usersSkipped')

    closed = BooleanField(default=False)
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
            "closed": self.closed,
            "data": self.task_data
        }

    def __unicode__(self):
        return unicode(self.id)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return unicode(self.id)


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

    @property
    def corrections(self):
        """
        Returns whole amount of actions/corrections given by user in this
        particular answer.

        :return: Count of corrections in this answer
        :rtype: int
        """
        raise NotImplementedError

    @corrections.setter
    def corrections(self, value):
        pass

    @corrections.deleter
    def corrections(self):
        pass

    def __unicode__(self):
        return unicode(self.pk)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return u"Report [%s by %s]".format(self.created_by, self.task)
