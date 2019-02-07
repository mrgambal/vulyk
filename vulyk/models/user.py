# -*- coding: utf-8 -*-
"""Module contains all models related to member entity."""

import datetime
from itertools import chain

from flask_login import UserMixin, AnonymousUserMixin
from flask_mongoengine import Document
from mongoengine import (
    StringField, BooleanField, DateTimeField, IntField, ReferenceField, PULL,
    ListField, signals, ValidationError)


class Group(Document):
    """
    Class was introduced to serve the permissions purpose
    """
    id = StringField(max_length=100, primary_key=True)
    description = StringField(max_length=200)
    allowed_types = ListField(StringField(max_length=100))

    meta = {'collection': 'groups'}

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return 'Group ID: {id}. Allowed types: {types}'.format(
            id=self.id,
            types=self.allowed_types)


class User(Document, UserMixin):
    """
    Main model for member entity.
    """
    username = StringField(max_length=200)
    password = StringField(max_length=200, default='')
    name = StringField(max_length=100)
    email = StringField()
    active = BooleanField(default=True)
    admin = BooleanField(default=False)
    groups = ListField(
        ReferenceField(Group, reverse_delete_rule=PULL, default=None))
    last_login = DateTimeField(default=datetime.datetime.now)
    processed = IntField(default=0)

    def is_active(self) -> bool:
        return self.active

    def is_admin(self) -> bool:
        return self.admin or False

    def is_eligible_for(self, task_type: str) -> bool:
        """
        Check that user is authorized to work with this tasks type

        :param task_type: Tasks type name
        :type task_type: str

        :return: True if user is eligible
        :rtype: bool

        :raises: AssertionError - if no `task_type` specified
        """
        assert task_type, 'Empty parameter `task_type` passed'

        return self.admin or task_type in chain(*(g.allowed_types for g in self.groups))

    def get_stats(self, task_type) -> dict:
        """
        Returns member's stats containing the number of tasks finished and
        the position in the global rank.

        :param task_type: Task type instance.
        :type task_type: vulyk.models.task_types.AbstractTaskType

        :return: Dictionary that contains total finished tasks count and the
                 position in the global rank.
        :rtype: dict[str, int]
        """
        leaders = task_type.get_leaders()
        i = 0
        prev_val = -1
        total = 0

        for user, freq in leaders:
            if freq != prev_val:
                i += 1
                prev_val = freq

            if user == self.id:
                total = freq
                break

        return {
            'total': total,
            'position': i
        }

    def as_dict(self) -> dict:
        """
        Converts the model-instance into a safe dict that will include some
        basic info about member.

        :return: Reduced set of information about member.
        :rtype: dict[str, str]
        """
        return {
            'username': self.username,
            'email': self.email
        }

    @classmethod
    def pre_save(cls, sender: type, document: Document, **kwargs: dict) -> Document:
        """
        A signal handler which will put a new member into a default group if
        any hasn't been assigned yet.

        :param sender: Type of signal emitter.
        :type sender: type
        :param document: New instance of User model.
        :type document: User
        :param kwargs: Additional parameters
        :type kwargs: dict

        :return: Modified User instance.
        :rtype: User
        """
        if all(map(lambda x: x.id != 'default', document.groups)):
            try:
                document.groups = [Group.objects.get(id='default')]
            except Group.DoesNotExist:
                raise Group.DoesNotExist('Please run \'manage.py init ...\'')

        return document

    @classmethod
    def get_by_id(cls, user_id: str) -> Document:
        """
        :param user_id: Needed user ID
        :type user_id: str

        :return: The user
        :rtype: User | None
        """
        try:
            return cls.objects.get(id=user_id)
        except (cls.DoesNotExist, ValidationError):
            return None

    def __str__(self) -> str:
        return self.username


class Anonymous(AnonymousUserMixin):
    name = 'Anonymous'


signals.pre_save.connect(User.pre_save, sender=User)
