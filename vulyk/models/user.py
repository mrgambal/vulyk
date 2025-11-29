# -*- coding: utf-8 -*-
"""Module contains all models related to member entity."""

import datetime
from datetime import timezone
from itertools import chain
from typing import TYPE_CHECKING, Any, ClassVar

from flask_login import AnonymousUserMixin, UserMixin
from flask_mongoengine.documents import Document
from mongoengine import (
    PULL,
    BooleanField,
    DateTimeField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
    ValidationError,
    signals,
)

if TYPE_CHECKING:
    from vulyk.models.task_types import AbstractTaskType


class Group(Document):
    """
    Class was introduced to serve the permissions purpose.
    """

    id = StringField(max_length=100, primary_key=True)
    description = StringField(max_length=200)
    allowed_types = ListField(StringField(max_length=100))

    meta: ClassVar[dict[str, str]] = {"collection": "groups"}

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return "Group ID: {id}. Allowed types: {types}".format(id=self.id, types=self.allowed_types)


class User(Document, UserMixin):
    """
    Main model for member entity.
    """

    username = StringField(max_length=200)
    password = StringField(max_length=200, default="")
    name = StringField(max_length=100)
    email = StringField()
    active = BooleanField(default=True)
    admin = BooleanField(default=False)
    groups = ListField(ReferenceField(Group, reverse_delete_rule=PULL, default=None))
    last_login = DateTimeField(default=lambda: datetime.datetime.now(timezone.utc))
    processed = IntField(default=0)

    def is_active(self) -> bool:
        return self.active

    def is_admin(self) -> bool:
        return self.admin or False

    def is_eligible_for(self, task_type: str) -> bool:
        """
        Check that user is authorized to work with this tasks type.

        :param task_type: Task type name.

        :return: True if user is eligible.

        :raises: ValueError - if no `task_type` specified
        """
        if not task_type:
            raise ValueError("Empty parameter `task_type` passed")

        return self.admin or task_type in chain(*(g.allowed_types for g in self.groups))

    def get_stats(self, task_type: "AbstractTaskType") -> dict[str, int]:
        """
        Returns member's stats containing the number of tasks finished and
        the position in the global rank.

        :param task_type: Task type instance.

        :return: dictionary that contains total finished tasks count and the
                 position in the global rank.
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

        return {"total": total, "position": i}

    def as_dict(self) -> dict[str, str]:
        """
        Converts the model-instance into a safe dict that will include some
        basic info about member.

        :return: Reduced set of information about member.
        """
        return {"username": self.username, "email": self.email}

    @classmethod
    def pre_save(cls, sender: type, document: Document, **kwargs: dict[str, Any]) -> Document:
        """
        A signal handler which will put a new member into a default group if
        any hasn't been assigned yet.

        :param sender: Type of signal emitter.
        :param document: New instance of User model.
        :param kwargs: Additional parameters.

        :return: Modified User instance.
        """
        if all((x.id != "default" for x in document.groups)):
            try:
                document.groups = [Group.objects.get(id="default")]
            except Group.DoesNotExist as err:
                raise Group.DoesNotExist("Please run 'manage.py init ...'") from err

        return document

    @classmethod
    def get_by_id(cls, user_id: str) -> Document | None:
        """
        :param user_id: Needed user ID.

        :return: The user.
        """
        try:
            return cls.objects.get(id=user_id)
        except (cls.DoesNotExist, ValidationError):
            return None

    def __str__(self) -> str:
        return self.username


class Anonymous(AnonymousUserMixin):
    name = "Anonymous"


signals.pre_save.connect(User.pre_save, sender=User)
