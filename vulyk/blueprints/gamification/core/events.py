# -*- coding: utf-8 -*-
"""
Here go all types of events to happen during the project's lifecycle.

By default all 'on task done' events add some non-zero amount of coins and
points. Achievements and levels are conditional things.

Another type of events is donations to some funds. These ones must contain
a link to a fund and negative amount of coins, along with zero points,
no achievements (at least – for now) and no level changes.
"""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar

from vulyk.models.tasks import AbstractAnswer
from vulyk.models.user import User

from ..core.foundations import Fund
from ..core.rules import Rule

__all__ = [
    "AchievementsEvent",
    "AchievementsLevelEvent",
    "DonateEvent",
    "Event",
    "InvalidEventException",
    "LevelEvent",
    "NoAchievementsEvent",
]


class InvalidEventException(BaseException):
    """
    Represents all possible errors during new event construction.
    """


class Event:
    """
    Generic gamification system event representation.

    Could reflect different type of events: task is done, user is being given
    points/money/achievements/new level etc, user donates coins to some fund.
    """

    __slots__: ClassVar[list[str]] = [
        "acceptor_fund",
        "achievements",
        "answer",
        "coins",
        "level_given",
        "points_given",
        "timestamp",
        "user",
        "viewed",
    ]

    def __init__(
        self,
        timestamp: datetime,
        user: User,
        answer: AbstractAnswer | None,
        points_given: Decimal,
        coins: Decimal,
        achievements: Sequence[Rule],
        acceptor_fund: Fund | None,
        level_given: int | None,
        *,
        viewed: bool,
    ) -> None:
        """Base event constructor"""
        self.timestamp = timestamp
        self.user = user
        self.answer = answer
        self.points_given = points_given
        self.coins = coins
        self.achievements = achievements
        self.acceptor_fund = acceptor_fund
        self.level_given = level_given
        self.viewed = viewed

        self._validate()

    def _validate(self) -> None:
        """
        :raises: InvalidEventException
        """
        is_donate = self.coins < 0 and self.acceptor_fund is not None
        is_bonus = self.coins > 0 and self.answer is None

        try:
            assert self.user is not None, "User should be present."

            if is_donate:
                assert self.points_given == 0, "No points are allowed for donate events"
                assert len(self.achievements) == 0, "No badges are allowed for donate events"
                assert self.level_given is None, "No levels are allowed for donate events"
                assert self.viewed, "Viewed property shall be set to True for donate events"
            else:
                assert self.acceptor_fund is None, "No acceptor funds are allowed for task events"
                assert self.coins >= 0, "No negative amount of coins are allowed for task events"
                assert self.level_given is None or self.level_given > 0, (
                    "New level must be greater than zero or be absent for task events"
                )
                assert self.points_given > 0, "Points amount must be positive for task events"

                if not is_bonus:
                    assert self.answer is not None, "Answer should be present for task events"

        except AssertionError as e:
            raise InvalidEventException(str(e)) from e

    @classmethod
    def build(
        cls,
        timestamp: datetime,
        user: User,
        answer: AbstractAnswer | None,
        points_given: Decimal,
        coins: Decimal,
        achievements: Sequence[Rule],
        acceptor_fund: Fund | None,
        level_given: int | None,
        *,
        viewed: bool,
    ) -> "Event":
        # validation stage
        ev = cls(
            timestamp=timestamp,
            user=user,
            answer=answer,
            points_given=points_given,
            coins=coins,
            achievements=achievements,
            acceptor_fund=acceptor_fund,
            level_given=level_given,
            viewed=viewed,
        )

        if ev.coins < 0 and ev.acceptor_fund is not None:
            return DonateEvent(timestamp=ev.timestamp, user=ev.user, coins=ev.coins, acceptor_fund=ev.acceptor_fund)
        if ev.level_given is None and len(ev.achievements) == 0:
            return NoAchievementsEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                viewed=ev.viewed,
            )
        if ev.level_given is not None and len(ev.achievements) == 0:
            return LevelEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                level_given=ev.level_given,
                viewed=ev.viewed,
            )
        if ev.level_given is None and len(ev.achievements) > 0:
            return AchievementsEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                achievements=ev.achievements,
                viewed=ev.viewed,
            )

        return AchievementsLevelEvent(
            timestamp=ev.timestamp,
            user=ev.user,
            answer=ev.answer,
            points_given=ev.points_given,
            coins=ev.coins,
            achievements=ev.achievements,
            level_given=ev.level_given,
            viewed=ev.viewed,
        )

    def to_dict(self, *, ignore_answer: bool = False) -> dict[str, Any]:
        """
        Could be used as a source for JSON or any other representation format.

        :param ignore_answer: Shows if the method should return answer as part of the dict
        """

        result = {
            "timestamp": self.timestamp,
            "user": self.user.username,
            "points_given": self.points_given,
            "coins": self.coins,
            "achievements": [r.to_dict() for r in self.achievements],
            "acceptor_fund": self.acceptor_fund.to_dict() if self.acceptor_fund is not None else None,
            "level_given": self.level_given,
            "viewed": self.viewed,
        }

        if not ignore_answer:
            result["answer"] = self.answer.as_dict() if self.answer is not None else None

        return result

    def __str__(self) -> str:
        return "Event({user}, {answer}, {points}, {coins}, {badges}, {lvl})".format(
            user=self.user.id,
            answer=self.answer.id if self.answer else None,
            points=self.points_given,
            coins=self.coins,
            badges=self.achievements,
            lvl=self.level_given,
        )

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False

        same_fund = (
            self.acceptor_fund == other.acceptor_fund
            if self.acceptor_fund is not None and other.acceptor_fund is not None
            else self.acceptor_fund is None and other.acceptor_fund is None
        )

        same_answer = (
            self.answer == other.answer
            if self.answer is not None and other.answer is not None
            else self.answer is None and other.answer is None
        )

        return (
            other.timestamp == self.timestamp
            and other.user.id == self.user.id
            and other.points_given == self.points_given
            and other.achievements == self.achievements
            and other.coins == self.coins
            and other.level_given == self.level_given
            and same_answer
            and same_fund
        )

    def __ne__(self, other: object) -> bool:
        return not self == other


class NoAchievementsEvent(Event):
    """
    Regular 'on task done' event that contains no new level or achievements
    assigned to user.
    """

    __slots__ = Event.__slots__

    def __init__(
        self,
        timestamp: datetime,
        user: User,
        answer: AbstractAnswer | None,
        points_given: Decimal,
        coins: Decimal,
        *,
        viewed: bool,
    ) -> None:
        super().__init__(
            timestamp=timestamp,
            user=user,
            answer=answer,
            points_given=points_given,
            coins=coins,
            achievements=[],
            acceptor_fund=None,
            level_given=None,
            viewed=viewed,
        )

    def __str__(self) -> str:
        return "NoAchievementsEvent({user}, {answer}, {points}, {coins})".format(
            user=self.user.id,
            answer=self.answer.id if self.answer else None,
            points=self.points_given,
            coins=self.coins,
        )


class AchievementsEvent(Event):
    """
    Regular 'on task done' event that contains only new achievements
    assigned to user.
    """

    __slots__ = Event.__slots__

    def __init__(
        self,
        timestamp: datetime,
        user: User,
        answer: AbstractAnswer | None,
        points_given: Decimal,
        coins: Decimal,
        achievements: Sequence[Rule],
        *,
        viewed: bool,
    ) -> None:
        super().__init__(
            timestamp=timestamp,
            user=user,
            answer=answer,
            points_given=points_given,
            coins=coins,
            achievements=achievements,
            acceptor_fund=None,
            level_given=None,
            viewed=viewed,
        )

    def __str__(self) -> str:
        return "AchievementsEvent({user}, {answer}, {points}, {coins}, {badges})".format(
            user=self.user.id,
            answer=self.answer.id if self.answer else None,
            points=self.points_given,
            coins=self.coins,
            badges=self.achievements,
        )


class LevelEvent(Event):
    """
    Regular 'on task done' event that contains only new level assigned to user.
    """

    __slots__ = Event.__slots__

    def __init__(
        self,
        timestamp: datetime,
        user: User,
        answer: AbstractAnswer | None,
        points_given: Decimal,
        coins: Decimal,
        level_given: int | None,
        *,
        viewed: bool,
    ) -> None:
        super().__init__(
            timestamp=timestamp,
            user=user,
            answer=answer,
            points_given=points_given,
            coins=coins,
            achievements=[],
            acceptor_fund=None,
            level_given=level_given,
            viewed=viewed,
        )

    def __str__(self) -> str:
        return "LevelEvent({user}, {answer}, {points}, {coins}, {lvl})".format(
            user=self.user.id,
            answer=self.answer.id if self.answer else None,
            points=self.points_given,
            coins=self.coins,
            lvl=self.level_given,
        )


class AchievementsLevelEvent(Event):
    """
    Regular 'on task done' event that contains both level and achievements
    assigned to user.
    """

    __slots__ = Event.__slots__

    def __init__(
        self,
        timestamp: datetime,
        user: User,
        answer: AbstractAnswer | None,
        points_given: Decimal,
        coins: Decimal,
        achievements: Sequence[Rule],
        level_given: int | None,
        *,
        viewed: bool,
    ) -> None:
        super().__init__(
            timestamp=timestamp,
            user=user,
            answer=answer,
            points_given=points_given,
            coins=coins,
            achievements=achievements,
            acceptor_fund=None,
            level_given=level_given,
            viewed=viewed,
        )

    def __str__(self) -> str:
        return "AchievementsLevelEvent({user}, {answer}, {points}, {coins}, {badges}, {lvl})".format(
            user=self.user.id,
            answer=self.answer.id if self.answer else None,
            points=self.points_given,
            coins=self.coins,
            badges=self.achievements,
            lvl=self.level_given,
        )


class DonateEvent(Event):
    """
    Regular 'on donate' event that contains negative amount of coins and
    a fund user donated to.
    `Viewed`-field is set to True as user itself triggers the action.
    """

    __slots__ = Event.__slots__

    def __init__(self, timestamp: datetime, user: User, coins: Decimal, acceptor_fund: Fund) -> None:
        super().__init__(
            timestamp=timestamp,
            user=user,
            answer=None,
            points_given=Decimal(0),
            coins=coins,
            achievements=[],
            acceptor_fund=acceptor_fund,
            level_given=None,
            viewed=True,
        )

    def __str__(self) -> str:
        return "DonateEvent({user}, {coins}, {acceptor_fund})".format(
            user=self.user.id, coins=self.coins, acceptor_fund=self.acceptor_fund
        )
