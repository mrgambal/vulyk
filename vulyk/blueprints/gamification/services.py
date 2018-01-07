# -*- coding: utf-8 -*-
"""
Services module
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from vulyk.blueprints.gamification.core.events import DonateEvent
from vulyk.blueprints.gamification.core.state import UserState
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.ext.worksession import WorkSessionManager
from vulyk.models.tasks import AbstractTask
from vulyk.models.user import User

__all__ = [
    'DonationResult',
    'DonationsService',
    'StatsService'
]


class DonationResult(Enum):
    """
    An enumeration to represent different results of donation process.
    """
    SUCCESS = 0
    STINGY = 1
    BEGGAR = 2
    LIAR = 3
    ERROR = 666


class DonationsService:
    """
    Class hides mildly complex donation logic from cruel outer world.
    """

    def __init__(self, user: User, fund_id: str, amount: Decimal) -> None:
        """
        Constructor.

        :param user: Current user
        :type user: User
        """
        self._amount = amount
        self._user = user
        self._fund = FundModel.find_by_id(fund_id)

    def donate(self) -> DonationResult:
        """
        Perform a donation process:
         - check if there is enough active money to spare
         - check if fund exists
         - try to decrease amount of coins on current account
         - create and save an event

        :return: One of `DonationResult` enum values:
            SUCCESS - everything went okay;
            STINGY - you tried to donate nothing;
            BEGGAR - you have less money than tried to spare;
            LIAR - you passed non-existent fund;
            ERROR - sh*t happened :( .
        :rtype: DonationResult
        """
        if self._amount <= 0:
            return DonationResult.STINGY

        if self._fund is None:
            return DonationResult.LIAR

        try:
            if UserStateModel.withdraw(user=self._user, amount=self._amount):
                EventModel.from_event(
                    DonateEvent(
                        timestamp=datetime.now(),
                        user=self._user,
                        coins=-self._amount,
                        acceptor_fund=self._fund)
                ).save()

                return DonationResult.SUCCESS
            else:
                return DonationResult.BEGGAR
        except (Exception, IOError):
            return DonationResult.ERROR


class StatsService:
    """
    Facade, the root stats collector to provide aggregated data from different
    repositories.
    """

    @classmethod
    def tasks_done_by_user(cls, user: User) -> int:
        """
        Returns optional of the total number of tasks were finished by user.

        :param user: Current user
        :type user: User

        :return: Number of tasks done or None
        :rtype: int
        """
        return EventModel.count_of_tasks_done_by_user(user)

    @classmethod
    def projects_count(cls, user: User) -> int:
        """
        Aggregate the number of batches in which user has done at least
        single tiny task.

        :param user: Current user
        :type user: User

        :return: Number of batches
        :rtype: int
        """
        return len(list(EventModel.batches_user_worked_on(user)))

    @classmethod
    def total_time_for_user(cls, user: User) -> int:
        """
        Count and return number of hours, spent on the site doing tasks.

        :param user: Current user
        :type user: User
        :return: Full hours
        :rtype: int
        """
        from vulyk.app import TASKS_TYPES

        seconds = 0

        for task_type in TASKS_TYPES.values():
            ws = task_type.work_session_manager  # type: WorkSessionManager
            # TODO: must be changed after time tracking on frontend is done
            seconds += ws.work_session.get_total_user_time_approximate(user.id)

        return seconds // 3600

    @classmethod
    def total_number_of_open_tasks(cls) -> int:
        """
        Count and return number of open tasks in all projects

        :return: Number of open tasks
        :rtype: int
        """

        return AbstractTask.objects.filter(closed=False).count()

    @classmethod
    def total_number_of_users(cls) -> int:
        """
        Count and return number of users registered in the system

        :return: Number of active users
        :rtype: int
        """

        return User.objects.filter(active=True).count()

    @classmethod
    def total_money_donated(cls) -> float:
        """
        Count and return total amount of money donated
        by all users to all foundations

        :return: Total amount in UAH
        :rtype: float
        """

        return EventModel.amount_of_money_donated(None)

    @classmethod
    def total_money_donated_by_user(cls, user: User) -> float:
        """
        Count and return total amount of money donated
        by current user

        :return: Total amount in UAH
        :rtype: float
        """

        return EventModel.amount_of_money_donated(user)

    @classmethod
    def state_of_user(cls, user: User) -> UserState:
        """
        Return current state of given user

        :return: Object which holds aggregated values
        on user current state for the registered user
        and None otherwise
        :rtype: UserState or None
        """

        if user.is_anonymous:
            return None

        return UserStateModel.get_or_create_by_user(user)
