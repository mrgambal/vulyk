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

from bson import ObjectId


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

    def __init__(self,
                 timestamp: datetime,
                 user_id: ObjectId,
                 answer_id: ObjectId,
                 points_given: int,
                 coins: int,
                 achievements: list,
                 acceptor_fund_id: ObjectId,
                 level_given: int,
                 viewed: bool) -> None:
        """
        Crap, I want python to have private constructors :(

        :type timestamp: datetime
        :type user_id: ObjectId
        :type answer_id: ObjectId | None
        :type points_given: int
        :type coins: int
        :type achievements: list[Rule]
        :type acceptor_fund_id: ObjectId | None
        :type level_given: int
        :type viewed: bool
        """
        self.timestamp = timestamp
        self.user_id = user_id
        self.answer_id = answer_id
        self.points_given = points_given
        self.coins = coins
        self.achievements = achievements
        self.acceptor_fund_id = acceptor_fund_id
        self.level_given = level_given
        self.viewed = viewed

        self._validate()

    def _validate(self):
        """

        :raises: InvalidEventException
        """
        is_donate = self.coins < 0 and self.acceptor_fund_id is not None

        try:
            assert self.user_id is not None, 'User should be present.'

            if is_donate:
                assert self.points_given == 0,\
                    'No points are allowed for donate events'
                assert len(self.achievements) == 0, \
                    'No badges are allowed for donate events'
                assert self.level_given is None,\
                    'No levels are allowed for donate events'
                assert self.viewed,\
                    'Viewed property shall be set to True for donate events'
            else:
                assert self.acceptor_fund_id is None, \
                    'No acceptor funds are allowed for task events'
                assert self.coins >= 0, \
                    'No negative amount of coins are allowed for task events'
                assert self.level_given >= 1 or self.level_given is None, \
                    'New level must be greater than zero or be absent' \
                    'for task events'
                assert self.points_given > 0, \
                    'Points amount must be positive for task events'
                assert self.answer_id is not None, \
                    'Answer should be present.for task events'

        except AssertionError as e:
            raise InvalidEventException(e)


class NoAchievementsEvent(Event):
    """
    Regular 'on task done' event that contains no new level or achievements
    assigned to user.
    """

    def __init__(self,
                 timestamp: datetime,
                 user_id: ObjectId,
                 answer_id: ObjectId,
                 points_given: int,
                 coins: int,
                 viewed: bool) -> None:
        """
        :type timestamp: datetime
        :type user_id: ObjectId
        :type answer_id: ObjectId | None
        :type points_given: int
        :type coins: int
        :type viewed: bool
        """
        super().__init__(timestamp=timestamp,
                         user_id=user_id,
                         answer_id=answer_id,
                         points_given=points_given,
                         coins=coins,
                         achievements=[],
                         acceptor_fund_id=None,
                         level_given=0,
                         viewed=viewed)


class AchievementsEvent(Event):
    """
    Regular 'on task done' event that contains only new achievements
    assigned to user.
    """

    def __init__(self,
                 timestamp: datetime,
                 user_id: ObjectId,
                 answer_id: ObjectId,
                 points_given: int,
                 coins: int,
                 achievements: list,
                 viewed: bool) -> None:
        """
        :type timestamp: datetime
        :type user_id: ObjectId
        :type answer_id: ObjectId | None
        :type points_given: int
        :type coins: int
        :type achievements: list[Rule]
        :type viewed: bool
        """
        super().__init__(timestamp=timestamp,
                         user_id=user_id,
                         answer_id=answer_id,
                         points_given=points_given,
                         coins=coins,
                         achievements=achievements,
                         acceptor_fund_id=None,
                         level_given=None,
                         viewed=viewed)


class LevelEvent(Event):
    """
    Regular 'on task done' event that contains only new level assigned to user.
    """

    def __init__(self,
                 timestamp: datetime,
                 user_id: ObjectId,
                 answer_id: ObjectId,
                 points_given: int,
                 coins: int,
                 level_given: int,
                 viewed: bool) -> None:
        """

        :type timestamp: datetime
        :type user_id: ObjectId
        :type answer_id: ObjectId | None
        :type points_given: int
        :type coins: int
        :type level_given: int
        :type viewed: bool
        """
        super().__init__(timestamp=timestamp,
                         user_id=user_id,
                         answer_id=answer_id,
                         points_given=points_given,
                         coins=coins,
                         achievements=[],
                         acceptor_fund_id=None,
                         level_given=level_given,
                         viewed=viewed)


class AchievementsLevelEvent(Event):
    """
    Regular 'on task done' event that contains both level and achievements
    assigned to user.
    """

    def __init__(self,
                 timestamp: datetime,
                 user_id: ObjectId,
                 answer_id: ObjectId,
                 points_given: int,
                 coins: int,
                 achievements: list,
                 level_given: int,
                 viewed: bool) -> None:
        """

        :type timestamp: datetime
        :type user_id: ObjectId
        :type answer_id: ObjectId | None
        :type points_given: int
        :type coins: int
        :type achievements: list[Rule]
        :type level_given: int
        :type viewed: bool
        """

        super().__init__(timestamp=timestamp,
                         user_id=user_id,
                         answer_id=answer_id,
                         points_given=points_given,
                         coins=coins,
                         achievements=achievements,
                         acceptor_fund_id=None,
                         level_given=level_given,
                         viewed=viewed)


class DonateEvent(Event):
    """
    Regular 'on donate' event that contains negative amount of coins and
    a fund user donated to.
    `Viewed`-field is set to True as user itself triggers the action.
    """

    def __init__(self,
                 timestamp: datetime,
                 user_id: ObjectId,
                 coins: int,
                 acceptor_fund_id: ObjectId) -> None:
        """
        :type timestamp: datetime
        :type user_id: ObjectId
        :type acceptor_fund_id: ObjectId | None
        :type coins: int
        """
        super().__init__(timestamp=timestamp,
                         user_id=user_id,
                         answer_id=None,
                         points_given=0,
                         coins=coins,
                         achievements=[],
                         acceptor_fund_id=acceptor_fund_id,
                         level_given=None,
                         viewed=True)
