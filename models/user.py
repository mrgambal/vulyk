# coding=utf-8
from mongoengine import StringField, EmailField, BooleanField, \
    DateTimeField, IntField
from flask.ext.login import UserMixin, AnonymousUserMixin
from flask.ext.mongoengine import Document
import datetime


class User(Document, UserMixin):
    username = StringField(max_length=200)
    password = StringField(max_length=200, default='')
    name = StringField(max_length=100)
    email = EmailField()
    active = BooleanField(default=True)
    admin = BooleanField(default=False)
    last_login = DateTimeField(default=datetime.datetime.now)
    processed = IntField(default=0)

    def is_active(self):
        return self.active

    def is_admin(self):
        return self.admin or False

    def __unicode__(self):
        return self.username


class Anonymous(AnonymousUserMixin):
    name = u"Anonymous"
