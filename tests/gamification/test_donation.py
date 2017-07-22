# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from decimal import Decimal
from tempfile import TemporaryFile
from unittest.mock import patch

from mongoengine import OperationError

from vulyk.blueprints.gamification.core.foundations import Fund
from vulyk.blueprints.gamification.core.state import UserState
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.services import (
    DonationResult, DonationsService)
from vulyk.models.user import Group, User

from .fixtures import FakeType
from ..base import BaseTest
from ..fixtures import FakeType as BaseFakeType


class TestDonation(BaseTest):
    FUND_ID = 'newfund'
    FUND_NAME = 'New fund'

    def setUp(self):
        Group.objects.create(
            description='test', id='default', allowed_types=[
                FakeType.type_name, BaseFakeType.type_name
            ])
        self.USER = User(username='user0', email='user0@email.com').save()

        super().setUp()

    def tearDown(self):
        super().tearDown()

        Group.objects.delete()
        User.objects.delete()
        EventModel.objects.delete()
        FundModel.objects.delete()
        FundModel._get_db().drop_collection('images.files')
        FundModel._get_db().drop_collection('images.chunks')

    def test_donation_service_success(self):
        fund = self._get_fund()
        amount = Decimal(100)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal(3000.67),
                actual_coins=Decimal(200),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now()
            )).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.SUCCESS,
                         'Donation result should be SUCCESS')
        self.assertEqual(state.actual_coins, Decimal(100),
                         'Actual coins value must be 100')

    def test_donation_service_success_event(self):
        fund = self._get_fund()
        amount = Decimal(100)
        UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal(3000.67),
                actual_coins=Decimal(200),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now()
            )).save()
        DonationsService(self.USER, fund.id, amount).donate()
        event = EventModel.objects.get(user=self.USER)

        self.assertTrue(event.coins, Decimal(-100))
        self.assertTrue(event.acceptor_fund.id, fund.id)

    def test_donation_service_beggar(self):
        fund = self._get_fund()
        amount = Decimal(200)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal(3000.67),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now()
            )).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.BEGGAR,
                         'Donation result should be BEGGAR')
        self.assertEqual(state.actual_coins, Decimal(100),
                         'Actual coins value must be 100')

    def test_donation_service_stingy_zero(self):
        fund = self._get_fund()
        amount = Decimal(0)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal(3000.67),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now()
            )).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.STINGY,
                         'Donation result for zero amount should be STINGY')
        self.assertEqual(state.actual_coins, Decimal(100),
                         'Actual coins value must be 100')

    def test_donation_service_stingy_negative(self):
        fund = self._get_fund()
        amount = Decimal(-10)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal(3000.67),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now()
            )).save()
        result = DonationsService(self.USER, fund.id, amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.STINGY,
                         'Donation result for negative amount must be STINGY')
        self.assertEqual(state.actual_coins, Decimal(100),
                         'Actual coins value must be 100')

    def test_donation_service_liar(self):
        amount = Decimal(100)
        state = UserStateModel.from_state(
            UserState(
                user=self.USER,
                level=0,
                points=Decimal(3000.67),
                actual_coins=Decimal(100),
                potential_coins=Decimal(500),
                achievements=[],
                last_changed=datetime.now()
            )).save()
        result = DonationsService(self.USER, "fund.id", amount).donate()
        state.reload()

        self.assertEqual(result, DonationResult.LIAR,
                         'Donation result should be LIAR')
        self.assertEqual(state.actual_coins, Decimal(100),
                         'Actual coins value must be 100')

    def test_donation_service_error(self):
        to_patch = 'vulyk.blueprints.gamification.models.state.' \
                   'UserStateModel.withdraw'

        def erroneous(user, amount):
            raise OperationError('oops')

        with patch(to_patch, erroneous):
            fund = self._get_fund()
            amount = Decimal(100)
            state = UserStateModel.from_state(
                UserState(
                    user=self.USER,
                    level=0,
                    points=Decimal(3000.67),
                    actual_coins=Decimal(100),
                    potential_coins=Decimal(500),
                    achievements=[],
                    last_changed=datetime.now()
                )).save()
            result = DonationsService(self.USER, fund.id, amount).donate()
            state.reload()

            self.assertEqual(result, DonationResult.ERROR,
                             'Donation result should be ERROR')
            self.assertEqual(state.actual_coins, Decimal(100),
                             'Actual coins value must be 100')

    def _get_fund(self) -> Fund:
        """
        :return: Fully fledged fund instance
        :rtype: Fund
        """
        fund_description = 'description'
        fund_site = 'site.com'
        fund_email = 'email@email.ek'
        load = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAbElEQVR' \
               b'4nO3Q0QmAMBAFwWitKSvFWsOKECIz/8c7dgwAAAAAAAAAAAAAADjHtW' \
               b'15zve3a333R3BvWT2UWIFYgViBWIFYgViBWIFYgViBWIFYgViBWIFYg' \
               b'ViBWIFYgVgAAAAAAAAAAAAAAPBTD1i3AiiQSFCiAAAAAElFTkSuQmCC'
        logo_bytes = base64.b64decode(load)

        with TemporaryFile('w+b', suffix='.jpg') as f:
            f.write(logo_bytes)

            fund = Fund(
                fund_id=self.FUND_ID,
                name=self.FUND_NAME,
                description=fund_description,
                site=fund_site,
                email=fund_email,
                logo=f,
                donatable=True)
            FundModel.from_fund(fund).save()

            return fund
