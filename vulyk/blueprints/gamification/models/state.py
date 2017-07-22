# -*- coding: utf-8 -*-
"""
Contains all DB models related to aggregated user state within the game
"""
from collections import Iterator
from decimal import Decimal
from enum import Enum

from flask_mongoengine import Document
from mongoengine import (
    IntField, ComplexDateTimeField, ReferenceField, ListField,
    DecimalField
)

from vulyk.models.user import User

from .rules import RuleModel
from ..core.state import UserState

__all__ = [
    'StateSortingKeys',
    'UserStateModel'
]


class StateSortingKeys(Enum):
    """
    The intent of this enum is to keep different sorting options shortcuts.
    """
    POINTS = 0
    ACTUAL_COINS = 1
    POTENTIAL_COINS = 2
    LEVEL = 3


class UserStateModel(Document):
    user = ReferenceField(document_type=User, required=True, unique=True)
    level = IntField(min_value=0, default=0)
    points = DecimalField(min_value=0, default=0)
    actual_coins = DecimalField(min_value=0, default=0, db_field='actualCoins')
    potential_coins = DecimalField(
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

    @classmethod
    def get_or_create_by_user(cls, user: User) -> UserState:
        """
        Returns an existing UserStateModel instance bound to the user, or a new
        one if didn't exist before.

        :param user: Current User model instance
        :type user: User

        :return: UserState instance
        :rtype: UserState
        """
        try:
            state_model = cls.objects.get(user=user)
        except cls.DoesNotExist:
            state_model = cls.objects.create(user=user)

        return state_model.to_state()

    @classmethod
    def update_state(cls, diff: UserState) -> None:
        """
        Prepares and conducts an atomic update query from passed diff.

        :param diff: State object contains values that are to be changed only.
        :type diff: UserState

        :rtype: None
        """
        update_dict = {'set__last_changed': diff.last_changed}

        if diff.level > 0:
            update_dict['set__level'] = diff.level
        if diff.points > 0:
            # DON'T PUT YOUR BLAME ON ME
            # https://github.com/MongoEngine/mongoengine/blob/master/mongoengine/fields.py#L415
            update_dict['inc__points'] = float(diff.points)
        if diff.actual_coins != 0:
            # ALL YOUR DECIMALS ARE BELONG TO US
            update_dict['inc__actual_coins'] = float(diff.actual_coins)
        if diff.potential_coins != 0:
            update_dict['inc__potential_coins'] = float(diff.potential_coins)
        if len(diff.achievements) > 0:
            update_dict['add_to_set__achievements'] = \
                cls.from_state(diff).achievements

        cls.objects.get(user=diff.user).update(**update_dict)

    @classmethod
    def get_top_users(cls, limit: int, sort_by: StateSortingKeys) -> Iterator:
        """
        Enumerates over top users basing on passed sorting criteria and
        limiting number. The yield sorting is descending.

        :param limit: Top limit
        :type limit: int
        :param sort_by: Criteria enumeration item
        :type sort_by: StateSortingKeys

        :return: An iterator
        :rtype: Iterator[UserState]
        """
        yield from map(
            lambda state_model: state_model.to_state(),
            cls.objects().order_by('-%s' % sort_by.name.lower()).limit(limit)
        )

    def __str__(self):
        return 'UserStateModel({model})'.format(model=str(self.to_state()))

    def __repr__(self):
        return str(self)

    @classmethod
    def withdraw(cls, user: User, amount: Decimal) -> bool:
        """
        Reflects money withdrawal from current account.

        :param user: User to perform the action on.
        :type user: User
        :param amount: Money amount (ONLY positive)
        :type amount: Decimal

        :raise:
            - RuntimeError – if amount is negative

        :return: True if needed amount was successfully withdrawn
        :rtype: bool
        """
        amount = float(amount)

        if amount <= 0:
            raise RuntimeError('Donation amount should be positive')

        update_dict = {'dec__actual_coins': amount}

        return cls.objects(user=user, actual_coins__gte=amount) \
                   .update(**update_dict) == 1
