# coding=utf-8
import datetime

from mongoengine import (
    StringField, IntField, DateTimeField, ListField,
    ReferenceField, DictField, CASCADE)
from flask.ext.mongoengine import Document
from slug import slug
from transliterate import translit

from models import User


class Task(Document):
    id = StringField(max_length=200, default='', primary_key=True)
    # TODO: discuss appropriate levels of priority
    priority = IntField(default=2, min_value=0, max_value=1)
    users_count = IntField(default=0, db_field='usersCount')
    users_processed = ListField(ReferenceField(User),
                                db_field='usersProcessed')

    title = StringField()
    text = StringField()
    structure = ListField(DictField())

    meta = {'collection': 'tasks'}

    def as_dict(self):
        return {"title": self.title,
                "id": self.id,
                "structure": self.structure}

    def set_id(self):
        if not self.id:
            self.id = slug(translit(self.title[:25], "uk", reversed=True))

        return self.id

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
