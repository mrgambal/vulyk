# -*- coding: utf-8 -*-
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from mongoengine import OperationError

from vulyk.blueprints.gamification.core.state import UserState
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.services import DonationResult, DonationsService
from vulyk.models.user import Group, User

from ..base import BaseTest
from ..fixtures import FakeType as BaseFakeType
from .fixtures import FakeType, FixtureFund


class TestDonation(BaseTest):
    USER: User

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            description="test", id="default", allowed_types=[FakeType.type_name, BaseFakeType.type_name]
        )
        cls.USER = User(username="user0", email="user0@email.com").save()

    @classmethod
    def tearDownClass(cls):
        Group.objects.delete()
        User.objects.delete()

        super().tearDownClass()

    def tearDown(self):
        super().tearDown()

        EventModel.objects.delete()
        FundModel.objects.delete()
        FundModel._get_db()["images.files"].drop()
        FundModel._get_db()["images.chunks"].drop()
        UserStateModel.objects.delete()

    def test_donation_service_success(self):
        fund = FixtureFund.get_fund()
        amount = Decimal(100)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(200),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.SUCCESS, "Donation result should be SUCCESS")
        self.assertEqual(state.actual_coins, Decimal(100), "Actual coins value must be 100")

    def test_donation_service_success_event(self):
        fund = FixtureFund.get_fund()
        amount = Decimal(100)
        UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(200),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        DonationsService(self.USER, fund.id, amount).donate()
        event = EventModel.objects.get(user=self.USER)

        self.assertEqual(event.coins, Decimal(-100))
        self.assertEqual(event.acceptor_fund.id, fund.id)

    def test_donation_service_two_success_events(self):
        fund = FixtureFund.get_fund()
        amount = Decimal(100)
        UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(500),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        event = EventModel.objects.get(user=self.USER)

        self.assertEqual(event.coins, Decimal(-100))
        self.assertEqual(result, DonationResult.SUCCESS)
        self.assertEqual(event.acceptor_fund.id, fund.id)

        amount = Decimal(50)
        result = DonationsService(self.USER, fund.id, amount).donate()
        event = EventModel.objects.filter(user=self.USER).order_by("-timestamp")[0]

        self.assertEqual(event.coins, Decimal(-50))
        self.assertEqual(result, DonationResult.SUCCESS)
        self.assertEqual(event.acceptor_fund.id, fund.id)

    def test_donation_service_beggar(self):
        fund = FixtureFund.get_fund()
        amount = Decimal(200)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.BEGGAR, "Donation result should be BEGGAR")
        self.assertEqual(state.actual_coins, Decimal(100), "Actual coins value must be 100")

    def test_donation_service_stingy_zero(self):
        fund = FixtureFund.get_fund()
        amount = Decimal(0)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.STINGY, "Donation result for zero amount should be STINGY")
        self.assertEqual(state.actual_coins, Decimal(100), "Actual coins value must be 100")

    def test_donation_service_stingy_negative(self):
        fund = FixtureFund.get_fund()
        amount = Decimal(-10)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.STINGY, "Donation result for negative amount must be STINGY")
        self.assertEqual(state.actual_coins, Decimal(100), "Actual coins value must be 100")

    def test_donation_service_liar(self):
        amount = Decimal(100)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal("3000.67"),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now(timezone.utc),
            )
        ).save()
        result = DonationsService(self.USER, "fund.id", amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.LIAR, "Donation result should be LIAR")
        self.assertEqual(state.actual_coins, Decimal(100), "Actual coins value must be 100")

    def test_donation_service_error(self):
        to_patch = "vulyk.blueprints.gamification.models.state.UserStateModel.withdraw"

        def erroneous(user, amount):
            raise OperationError("oops")

        with patch(to_patch, erroneous):
            fund = FixtureFund.get_fund()
            amount = Decimal(100)
            state = UserStateModel.from_state(
                UserState(
                    user=self.USER,
                    level=0,
                    points=Decimal("3000.67"),
                    actual_coins=Decimal(100),
                    potential_coins=Decimal(500),
                    achievements=[],
                    last_changed=datetime.now(timezone.utc),
                )
            ).save()
            result = DonationsService(self.USER, fund.id, amount).donate()
            state.reload()

            self.assertEqual(result, DonationResult.ERROR, "Donation result should be ERROR")
            self.assertEqual(state.actual_coins, Decimal(100), "Actual coins value must be 100")
            return fund


if __name__ == "__main__":
    unittest.main()
