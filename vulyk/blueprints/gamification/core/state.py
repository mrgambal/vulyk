# -*- coding: utf-8 -*-
"""
The package contains user state model and everything that will belong to
this part of domain.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from vulyk.models.user import User

__all__ = ["UserState"]


class InvalidUserStateException(BaseException):
    """
    Generic container for all types of error may happen during
    user state construction.
    """


class UserState:
    """
    An aggregation of all the stuff user has gotten working on projects so far.
    """

    __slots__ = ["achievements", "actual_coins", "last_changed", "level", "points", "potential_coins", "user"]

    def __init__(
        self,
        user: User,
        level: int,
        points: Decimal,
        actual_coins: Decimal,
        potential_coins: Decimal,
        achievements: list,
        last_changed: datetime,
    ) -> None:
        """
        :param user: User instance.
        :param level: User level.
        :param points: Total points earned.
        :param actual_coins: Current coins balance.
        :param potential_coins: Potential coins to be earned.
        :param achievements: List of user achievements.
        :param last_changed: Last modification timestamp.
        """
        self.user = user
        self.level = level
        self.points = points
        self.actual_coins = actual_coins
        self.potential_coins = potential_coins
        self.achievements = {a.id: a for a in achievements}
        self.last_changed = last_changed

        self._validate()

    def _validate(self) -> None:
        """
        Keep the internal structure valid.

        :raises InvalidUserStateException: if any validation fails.
        """
        if self.user is None:
            raise InvalidUserStateException("User must be present.")
        if self.level < 0:
            raise InvalidUserStateException("Level value must be zero or greater.")
        if self.points < Decimal(0):
            raise InvalidUserStateException("Points value must be zero or greater.")
        if self.actual_coins < Decimal(0):
            raise InvalidUserStateException("Actual coins value must be zero or greater.")
        if self.potential_coins < Decimal(0):
            raise InvalidUserStateException("Potential coins value must be zero or greater.")
        if not isinstance(self.achievements, dict):
            raise InvalidUserStateException("Achievements value must be a dict.")
        if not isinstance(self.last_changed, datetime) or self.last_changed.tzinfo is None:
            raise InvalidUserStateException("Last changed value must be a datetime.")

    def to_dict(self) -> dict[str, Any]:
        """
        Could be used as a source for JSON or any other representation format.

        :return: Dict-ized object view.
        """
        return {
            "user": str(self.user.username),
            "level": self.level,
            "points": self.points,
            "actual_coins": self.actual_coins,
            "potential_coins": self.potential_coins,
            "achievements": [r.to_dict() for r in self.achievements.values()],
            "last_changed": self.last_changed.strftime("%d.%m.%Y %H:%M:%S"),
        }

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, UserState):
            return False

        return (
            o.user.username == self.user.username
            and o.level == self.level
            and o.points == self.points
            and o.actual_coins == self.actual_coins
            and o.potential_coins == self.potential_coins
            and (set(o.achievements.keys()) == set(self.achievements.keys()))
            and o.last_changed == self.last_changed
        )

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return "UserState({user}, {level}, {points}, {act_coins}, {pot_coins}, {badges}, {changed})".format(
            user=self.user.username,
            level=self.level,
            points=self.points,
            act_coins=self.actual_coins,
            pot_coins=self.potential_coins,
            badges=self.achievements.keys(),
            changed=self.last_changed,
        )

    def __repr__(self) -> str:
        return str(self)
