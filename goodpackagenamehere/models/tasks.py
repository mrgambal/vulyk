# coding=utf-8
import datetime

from mongoengine import (
    StringField, IntField, DateTimeField, ListField,
    ReferenceField, DictField, CASCADE)
from flask.ext.mongoengine import Document

from . import User


class AbstractTask(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    task_type = StringField(max_length=50, required=True)
    users_count = IntField(default=0, db_field='usersCount')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')

    task_data = DictField()

    meta = {
        'collection': 'tasks',
        'allow_inheritance': True,
        'indexes': [
            'task_type'
        ]
    }

    def as_dict(self):
        return {"title": self.title,
                "id": self.id}

    def __unicode__(self):
        return unicode(self.id)

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return unicode(self.title)


# Not sure about this one as well
# class Report(Document):
#     task = ReferenceField(Task, reverse_delete_rule=CASCADE)
#     created_by = ReferenceField(User, reverse_delete_rule=CASCADE,
#                                 db_field="createdBy")
#     created_at = DateTimeField(default=datetime.datetime.now,
#                                db_field="createdAt")
#     # not sure - could be extended
#     found_mistakes = ListField(DictField(), db_field="foundMistakes")

#     meta = {'collection': 'reports'}

#     def __unicode__(self):
#         return unicode(self.pk)

#     def __str__(self):
#         return self.__unicode__()

#     def __repr__(self):
#         return u"Report [%s by %s]".format(self.created_by, self.task)
