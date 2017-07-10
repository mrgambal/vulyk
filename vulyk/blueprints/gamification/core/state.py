# -*- coding: utf-8 -*-
"""
The package contains user state model and everything that will belong to
this part of domain.
"""
from datetime import datetime

from vulyk.models.user import User

__all__ = [
    'UserState'
]


class InvalidUserStateException(BaseException):
    """
    Generic container for all types of error may happen during
    user state construction.
    """
    pass


class UserState:
    """
    An aggregation of all the stuff user has gotten working on projects so far.
    """
    __slots__ = [
        'user',
        'level',
        'points',
        'actual_coins',
        'potential_coins',
        'achievements',
        'last_changed'
    ]

    def __init__(self,
                 user: User,
                 level: int,
                 points: int,
                 actual_coins: int,
                 potential_coins: int,
                 achievements: list,
                 last_changed: datetime) -> None:
        """
        :type user: User
        :type level: int
        :type points: int
        :type actual_coins: int
        :type potential_coins: int
        :type achievements: list[vulyk.blueprints.gamification.core.rules.Rule]
        :type last_changed: datetime
        """
        self.user = user
        self.level = level
        self.points = points
        self.actual_coins = actual_coins
        self.potential_coins = potential_coins
        self.achievements = {a.id: a for a in achievements}
        self.last_changed = last_changed

        self._validate()

    def _validate(self):
        """
        Keep the internal structure valid.

        :raises: InvalidUserStateException
        """
        try:
            assert self.user is not None, 'User must be present.'
            assert self.level >= 0, 'Level value must be zero or greater.'
            assert self.points >= 0, 'Points value must be zero or greater.'
            assert self.actual_coins >= 0, \
                'Actual coins value must be zero or greater.'
            assert self.potential_coins >= 0, \
                'Potential coins value must be zero or greater.'
            assert isinstance(self.achievements, dict), \
                'Achievements value must be a dict'
            assert isinstance(self.last_changed, datetime), \
                'Achievements value must be a datetime'
        except AssertionError as e:
            raise InvalidUserStateException(e)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, self.__class__):
            return o.user.id == self.user.id \
                   and o.level == self.level \
                   and o.points == self.points \
                   and o.actual_coins == self.actual_coins \
                   and o.potential_coins == self.potential_coins \
                   and set(o.achievements.keys()) \
                       == set(self.achievements.keys()) \
                   and o.last_changed == self.last_changed

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return 'UserState({user}, {level}, {points}, {act_coins}, ' \
               '{pot_coins}, {badges}, {changed})' \
            .format(user=self.user.id,
                    level=self.level,
                    points=self.points,
                    act_coins=self.actual_coins,
                    pot_coins=self.potential_coins,
                    badges=self.achievements.keys(),
                    changed=self.last_changed)

    def __repr__(self) -> str:
        return str(self)
