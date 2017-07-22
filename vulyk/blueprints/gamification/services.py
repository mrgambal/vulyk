# -*- coding: utf-8 -*-
"""
Services module
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from vulyk.blueprints.gamification.core.events import DonateEvent
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.models.user import User

__all__ = [
    'DonationResult',
    'DonationsService'
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
