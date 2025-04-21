# -*- coding: utf-8 -*-
"""
Contains all DB models related to aggregated user state within the game
"""

from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from bson import ObjectId
from flask_mongoengine.documents import Document
from mongoengine import DecimalField, IntField, ListField, ReferenceField

from vulyk.models.user import User

from ..core.state import UserState
from .fields import UTCComplexDateTimeField
from .rules import RuleModel

__all__ = ["StateSortingKeys", "UserStateModel"]


class StateSortingKeys(Enum):
    """
    The intent of this enum is to keep different sorting options shortcuts.
    """

    POINTS = 0
    ACTUAL_COINS = 1
    POTENTIAL_COINS = 2
    LEVEL = 3


class UserStateModel(Document):
    """User state in the gamification system"""

    user: User = ReferenceField(document_type=User, required=True, unique=True)
    level: int = IntField(min_value=0, default=0)
    # As for mongoengine 0.17.0 the min_value parameter governs not the field
    # value only, but every influx value as well.
    # E.g. the field has value of Decimal(100) and one wants to decrease by 1.
    # The change mutates from points__dec: Decimal(1)
    # to points__inc: Decimal(-1), and then the value Decimal(-1)
    # is validated against self.min_value = 0.
    # Even if the result is supposed to be 99, validation will fail as -1 < 0.
    points: Decimal = DecimalField(default=0)
    actual_coins: Decimal = DecimalField(default=0, db_field="actualCoins")
    potential_coins: Decimal = DecimalField(default=0, db_field="potentialCoins")
    achievements: list[RuleModel] = ListField(field=ReferenceField(document_type=RuleModel, required=False))
    last_changed: datetime = UTCComplexDateTimeField(db_field="lastChanged", default=lambda: datetime.now(timezone.utc))

    meta: ClassVar[dict[str, str | bool | list[str]]] = {
        "collection": "gamification.userState",
        "allow_inheritance": True,
        "indexes": ["user", "last_changed"],
    }

    def to_state(self) -> UserState:
        """
        DB-specific model to UserState converter.

        It isn't supposed to dig out what's been buried once, yet this method
        is really useful for tests.

        :return: New UserState instance.
        """
        return UserState(
            user=self.user,
            level=self.level,
            points=self.points,
            actual_coins=self.actual_coins,
            potential_coins=self.potential_coins,
            achievements=[r.to_rule() for r in self.achievements if hasattr(r, "to_rule")],
            last_changed=self.last_changed.replace(tzinfo=timezone.utc),
        )

    @classmethod
    def from_state(cls, state: UserState) -> "UserStateModel":
        """
        UserState to DB-specific model converter.

        :param state: Source user state.
        :return: New model instance.
        """
        return cls(
            user=state.user,
            level=state.level,
            points=state.points,
            actual_coins=state.actual_coins,
            potential_coins=state.potential_coins,
            achievements=RuleModel.objects(id__in=[r.id for r in state.achievements.values()]),
            last_changed=state.last_changed,
        )

    @classmethod
    def get_or_create_by_user(cls, user: User) -> UserState:
        """
        Returns an existing UserStateModel instance bound to the user, or a new
        one if didn't exist before.

        :param user: Current User model instance.
        :return: UserState instance.
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
        :return: None.
        """
        update_dict: dict[str, Any] = {"set__last_changed": diff.last_changed}

        if diff.level > 0:
            update_dict["set__level"] = diff.level
        if diff.points > 0:
            # DON'T PUT YOUR BLAME ON ME
            # https://github.com/MongoEngine/mongoengine/blob/master/mongoengine/fields.py#L415
            update_dict["inc__points"] = float(diff.points)
        if diff.actual_coins != 0:
            # ALL YOUR DECIMALS ARE BELONG TO US
            update_dict["inc__actual_coins"] = float(diff.actual_coins)
        if diff.potential_coins != 0:
            update_dict["inc__potential_coins"] = float(diff.potential_coins)
        if diff.achievements:
            update_dict["add_to_set__achievements"] = cls.from_state(diff).achievements

        try:
            cls.objects.get(user=diff.user).update(**update_dict)
        except cls.DoesNotExist:
            cls.objects.create(user=diff.user)

    @classmethod
    def get_top_users(cls, limit: int, sort_by: StateSortingKeys) -> Iterator[UserState]:
        """
        Enumerates over top users basing on passed sorting criteria and
        limiting number. The yield sorting is descending.

        :param limit: Top limit.
        :param sort_by: Criteria enumeration item.
        :return: An iterator over UserState objects.
        """
        yield from (
            state_model.to_state() for state_model in cls.objects().order_by("-%s" % sort_by.name.lower()).limit(limit)
        )

    def __str__(self) -> str:
        return "UserStateModel({model})".format(model=str(self.to_state()))

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def withdraw(cls, user: User, amount: Decimal) -> bool:
        """
        Reflects money withdrawal from current account.

        :param user: User to perform the action on.
        :param amount: Money amount (ONLY positive).
        :raises RuntimeError: if amount is negative.
        :return: True if needed amount was successfully withdrawn.
        """
        if amount <= 0:
            raise RuntimeError("Donation amount should be positive")

        update_dict = {"dec__actual_coins": amount}

        return cls.objects(user=user, actual_coins__gte=amount).update(**update_dict) == 1

    @classmethod
    def transfer_coins_to_actual(cls, uid: ObjectId, amount: Decimal) -> bool:
        """
        :param uid: Current user ID.
        :param amount: Money amount.
        :return: True if success.
        """
        result = cls.objects(user=uid, potential_coins__gte=amount).update_one(
            inc__actual_coins=amount, dec__potential_coins=amount
        )

        return result == 1
