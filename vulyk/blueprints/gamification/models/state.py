# -*- coding: utf-8 -*-
"""
Contains all DB models related to aggregated user state within the game
"""
from flask_mongoengine import Document
from mongoengine import (
    IntField, ComplexDateTimeField, ReferenceField, ListField
)

from vulyk.models.user import User

from .rules import RuleModel
from ..core.state import UserState

__all__ = [
    'UserStateModel'
]


class UserStateModel(Document):
    user = ReferenceField(document_type=User, required=True, unique=True)
    level = IntField(min_value=0, default=0)
    points = IntField(min_value=0, default=0)
    actual_coins = IntField(min_value=0, default=0, db_field='actualCoins')
    potential_coins = IntField(
        min_value=0, default=0, db_field='potentialCoins')
    achievements = ListField(
        field=ReferenceField(document_type=RuleModel, required=False))
    last_changed = ComplexDateTimeField(db_field='lastChanged')

    meta = {
        'collection': 'gamification.userState',
        'allow_inheritance': True,
        'indexes': [
            'user',
            'last_changed'
        ]
    }

    def to_state(self) -> UserState:
        """
        DB-specific model to UserState converter.

        It isn't supposed to dig out what's been buried once, yet this method
        is really useful for tests.

        :return: New UserState instance
        :rtype: UserState
        """
        return UserState(
            user=self.user,
            level=self.level,
            points=self.points,
            actual_coins=self.actual_coins,
            potential_coins=self.potential_coins,
            achievements=[r.to_rule() for r in self.achievements],
            last_changed=self.last_changed
        )

    @classmethod
    def from_state(cls, state: UserState):
        """
        UserState to DB-specific model converter.

        :param state: Source user state
        :type state: UserState

        :return: New model instance
        :rtype: UserStateModel
        """
        return cls(
            user=state.user,
            level=state.level,
            points=state.points,
            actual_coins=state.actual_coins,
            potential_coins=state.potential_coins,
            achievements=RuleModel.objects(
                id__in=[r.id for r in state.achievements.values()]),
            last_changed=state.last_changed
        )

    def __str__(self):
        return str(self.to_state())

    def __repr__(self):
        return str(self)
