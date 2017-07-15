# -*- coding: utf-8 -*-
"""
Here go all types of events to happen during the project's lifecycle.

By default all 'on task done' events add some non-zero amount of coins and
points. Achievements and levels are conditional things.

Another type of events is donations to some funds. These ones must contain
a link to a fund and negative amount of coins, along with zero points,
no achievements (at least – for now) and no level changes.
"""
from datetime import datetime

from vulyk.models.tasks import AbstractAnswer
from vulyk.models.user import User

from ..core.foundations import Fund

__all__ = [
    'InvalidEventException',
    'Event',
    'NoAchievementsEvent',
    'AchievementsEvent',
    'AchievementsLevelEvent',
    'LevelEvent',
    'DonateEvent'
]


class InvalidEventException(BaseException):
    """
    Represents all possible errors during new event construction.
    """
    pass


class Event:
    """
    Generic gamification system event representation.

    Could reflect different type of events: task is done, user is being given
    points/money/achievements/new level etc, user donates coins to some fund.
    """
    __slots__ = [
        'timestamp',
        'user',
        'answer',
        'points_given',
        'coins',
        'achievements',
        'acceptor_fund',
        'level_given',
        'viewed'
    ]

    def __init__(self,
                 timestamp: datetime,
                 user: User,
                 answer: AbstractAnswer,
                 points_given: int,
                 coins: int,
                 achievements: list,
                 acceptor_fund: Fund,
                 level_given: int,
                 viewed: bool) -> None:
        """
        Crap, I want python to have private constructors :(

        :type timestamp: datetime
        :type user: User
        :type answer: AbstractAnswer | None
        :type points_given: int
        :type coins: int
        :type achievements: list[Rule]
        :type acceptor_fund: Fund
        :type level_given: int
        :type viewed: bool
        """
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

    def _validate(self):
        """

        :raises: InvalidEventException
        """
        is_donate = self.coins < 0 and self.acceptor_fund is not None

        try:
            assert self.user is not None, 'User should be present.'

            if is_donate:
                assert self.points_given == 0, \
                    'No points are allowed for donate events'
                assert len(self.achievements) == 0, \
                    'No badges are allowed for donate events'
                assert self.level_given is None, \
                    'No levels are allowed for donate events'
                assert self.viewed, \
                    'Viewed property shall be set to True for donate events'
            else:
                assert self.acceptor_fund is None, \
                    'No acceptor funds are allowed for task events'
                assert self.coins >= 0, \
                    'No negative amount of coins are allowed for task events'
                assert self.level_given is None or self.level_given > 0, \
                    'New level must be greater than zero or be absent ' \
                    'for task events'
                assert self.points_given > 0, \
                    'Points amount must be positive for task events'
                assert self.answer is not None, \
                    'Answer should be present for task events'

        except AssertionError as e:
            raise InvalidEventException(e)

    @classmethod
    def build(cls: type,
              timestamp: datetime,
              user: User,
              answer: AbstractAnswer,
              points_given: int,
              coins: int,
              achievements: list,
              acceptor_fund: Fund,
              level_given: int,
              viewed: bool):
        """
        Fabric method

        :type timestamp: datetime
        :type user: User
        :type answer: AbstractAnswer | None
        :type points_given: int
        :type coins: int
        :type achievements: list[Rule]
        :type acceptor_fund: Fund | None
        :type level_given: int
        :type viewed: bool

        :rtype: Event
        """
        # validation stage
        ev = cls(timestamp=timestamp,
                 user=user,
                 answer=answer,
                 points_given=points_given,
                 coins=coins,
                 achievements=achievements,
                 acceptor_fund=acceptor_fund,
                 level_given=level_given,
                 viewed=viewed)

        if ev.coins < 0 and ev.acceptor_fund is not None:
            return DonateEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                coins=ev.coins,
                acceptor_fund=ev.acceptor_fund)
        elif ev.level_given is None and len(ev.achievements) == 0:
            return NoAchievementsEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                viewed=ev.viewed)
        elif ev.level_given is not None and len(ev.achievements) == 0:
            return LevelEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                level_given=ev.level_given,
                viewed=ev.viewed)
        elif ev.level_given is None and len(ev.achievements) > 0:
            return AchievementsEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                achievements=ev.achievements,
                viewed=ev.viewed)
        else:
            return AchievementsLevelEvent(
                timestamp=ev.timestamp,
                user=ev.user,
                answer=ev.answer,
                points_given=ev.points_given,
                coins=ev.coins,
                achievements=ev.achievements,
                level_given=ev.level_given,
                viewed=ev.viewed)

    def to_dict(self) -> dict:
        """
        Could be used as a source for JSON or any other representation format

        :return: Dict-ized object view
        :rtype: dict
        """
        return {
            'timestamp': self.timestamp,
            'user': self.user.username,
            'answer': self.answer.as_dict()
                if self.answer is not None
                else None,
            'points_given': self.points_given,
            'coins': self.coins,
            'achievements': [r.to_dict() for r in self.achievements],
            'acceptor_fund': self.acceptor_fund.to_dict()
                if self.acceptor_fund is not None
                else None,
            'level_given': self.level_given,
            'viewed': self.viewed
        }

    def __str__(self):
        return 'Event({user}, {answer}, {points}, {coins}, {badges}, {lvl})' \
            .format(user=self.user.id,
                    answer=self.answer.id,
                    points=self.points_given,
                    coins=self.coins,
                    badges=self.achievements,
                    lvl=self.level_given)

    def __repr__(self):
        return str(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            same_fund = False
            same_answer = False

            if self.acceptor_fund is None:
                same_fund = other.acceptor_fund is None
            else:
                same_fund = self.acceptor_fund == other.acceptor_fund

            if self.answer is None:
                same_answer = other.answer is None
            else:
                same_answer = self.answer == other.answer

            return other.timestamp == self.timestamp \
                and other.user.id == self.user.id \
                and other.points_given == self.points_given \
                and other.achievements == self.achievements \
                and other.coins == self.coins \
                and other.level_given == self.level_given \
                and same_answer and same_fund
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self == other


class NoAchievementsEvent(Event):
    """
    Regular 'on task done' event that contains no new level or achievements
    assigned to user.
    """
    __slots__ = Event.__slots__

    def __init__(self,
                 timestamp: datetime,
                 user: User,
                 answer: AbstractAnswer,
                 points_given: int,
                 coins: int,
                 viewed: bool) -> None:
        """
        :type timestamp: datetime
        :type user: User
        :type answer: AbstractAnswer | None
        :type points_given: int
        :type coins: int
        :type viewed: bool
        """
        super().__init__(timestamp=timestamp,
                         user=user,
                         answer=answer,
                         points_given=points_given,
                         coins=coins,
                         achievements=[],
                         acceptor_fund=None,
                         level_given=None,
                         viewed=viewed)

    def __str__(self):
        return 'NoAchievementsEvent({user}, {answer}, {points}, {coins})' \
            .format(user=self.user.id,
                    answer=self.answer.id,
                    points=self.points_given,
                    coins=self.coins)


class AchievementsEvent(Event):
    """
    Regular 'on task done' event that contains only new achievements
    assigned to user.
    """
    __slots__ = Event.__slots__

    def __init__(self,
                 timestamp: datetime,
                 user: User,
                 answer: AbstractAnswer,
                 points_given: int,
                 coins: int,
                 achievements: list,
                 viewed: bool) -> None:
        """
        :type timestamp: datetime
        :type user: User
        :type answer: AbstractAnswer | None
        :type points_given: int
        :type coins: int
        :type achievements: list[Rule]
        :type viewed: bool
        """
        super().__init__(timestamp=timestamp,
                         user=user,
                         answer=answer,
                         points_given=points_given,
                         coins=coins,
                         achievements=achievements,
                         acceptor_fund=None,
                         level_given=None,
                         viewed=viewed)

    def __str__(self):
        return 'AchievementsEvent(' \
               '{user}, {answer}, {points}, {coins}, {badges})' \
            .format(user=self.user.id,
                    answer=self.answer.id,
                    points=self.points_given,
                    coins=self.coins,
                    badges=self.achievements)


class LevelEvent(Event):
    """
    Regular 'on task done' event that contains only new level assigned to user.
    """
    __slots__ = Event.__slots__

    def __init__(self,
                 timestamp: datetime,
                 user: User,
                 answer: AbstractAnswer,
                 points_given: int,
                 coins: int,
                 level_given: int,
                 viewed: bool) -> None:
        """

        :type timestamp: datetime
        :type user: User
        :type answer: AbstractAnswer | None
        :type points_given: int
        :type coins: int
        :type level_given: int
        :type viewed: bool
        """
        super().__init__(timestamp=timestamp,
                         user=user,
                         answer=answer,
                         points_given=points_given,
                         coins=coins,
                         achievements=[],
                         acceptor_fund=None,
                         level_given=level_given,
                         viewed=viewed)

    def __str__(self):
        return 'LevelEvent({user}, {answer}, {points}, {coins}, {lvl})' \
            .format(user=self.user.id,
                    answer=self.answer.id,
                    points=self.points_given,
                    coins=self.coins,
                    lvl=self.level_given)


class AchievementsLevelEvent(Event):
    """
    Regular 'on task done' event that contains both level and achievements
    assigned to user.
    """
    __slots__ = Event.__slots__

    def __init__(self,
                 timestamp: datetime,
                 user: User,
                 answer: AbstractAnswer,
                 points_given: int,
                 coins: int,
                 achievements: list,
                 level_given: int,
                 viewed: bool) -> None:
        """

        :type timestamp: datetime
        :type user: User
        :type answer: AbstractAnswer | None
        :type points_given: int
        :type coins: int
        :type achievements: list[vulyk.blueprints.gamification.core.rules.Rule]
        :type level_given: int
        :type viewed: bool
        """

        super().__init__(timestamp=timestamp,
                         user=user,
                         answer=answer,
                         points_given=points_given,
                         coins=coins,
                         achievements=achievements,
                         acceptor_fund=None,
                         level_given=level_given,
                         viewed=viewed)

    def __str__(self):
        return 'AchievementsLevelEvent(' \
               '{user}, {answer}, {points}, {coins}, {badges}, {lvl})' \
            .format(user=self.user.id,
                    answer=self.answer.id,
                    points=self.points_given,
                    coins=self.coins,
                    badges=self.achievements,
                    lvl=self.level_given)


class DonateEvent(Event):
    """
    Regular 'on donate' event that contains negative amount of coins and
    a fund user donated to.
    `Viewed`-field is set to True as user itself triggers the action.
    """
    __slots__ = Event.__slots__

    def __init__(self,
                 timestamp: datetime,
                 user: User,
                 coins: int,
                 acceptor_fund: Fund) -> None:
        """
        :type timestamp: datetime
        :type user: User
        :type acceptor_fund: Fund
        :type coins: int
        """
        super().__init__(timestamp=timestamp,
                         user=user,
                         answer=None,
                         points_given=0,
                         coins=coins,
                         achievements=[],
                         acceptor_fund=acceptor_fund,
                         level_given=None,
                         viewed=True)

    def __str__(self):
        return 'DonateEvent({user}, {coins}, {acceptor_fund})' \
            .format(user=self.user.id,
                    coins=self.coins,
                    acceptor_fund=self.acceptor_fund)
