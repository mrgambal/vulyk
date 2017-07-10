# -*- coding: utf-8 -*-
"""
test_event_models
"""
import base64
from datetime import datetime
from tempfile import TemporaryFile

from vulyk.blueprints.gamification.core.events import (
    Event, NoAchievementsEvent, LevelEvent, AchievementsEvent,
    AchievementsLevelEvent, DonateEvent)
from vulyk.blueprints.gamification.core.foundations import Fund
from vulyk.blueprints.gamification.core.rules import Rule
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk.blueprints.gamification.models.rules import RuleModel
from vulyk.models.tasks import AbstractTask, AbstractAnswer
from vulyk.models.user import Group, User

from ..base import BaseTest
from ..fixtures import FakeType


class TestEventModels(BaseTest):
    TASK_TYPE = FakeType.type_name
    USER = None
    TASK = None
    ANSWER = None
    TIMESTAMP = datetime.now()

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])
        self.USER = User(username='user0', email='user0@email.com').save()
        self.TASK = FakeType.task_model(
            id='task1',
            task_type=self.TASK_TYPE,
            batch='default',
            closed=False,
            users_count=0,
            users_processed=[],
            task_data={'data': 'data'}).save()
        self.ANSWER = FakeType.answer_model(
            task=self.TASK,
            created_by=self.USER,
            created_at=datetime.now(),
            task_type=self.TASK_TYPE,
            result={}).save()

    def tearDown(self):
        super().tearDown()

        User.objects.delete()
        Group.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()

        EventModel.objects.delete()
        FundModel.objects.delete()
        RuleModel.objects.delete()

    def test_no_achievements_ok(self):
        ev = Event.build(
            timestamp=self.TIMESTAMP,
            user=self.USER,
            answer=self.ANSWER,
            points_given=10,
            coins=10,
            achievements=[],
            acceptor_fund=None,
            level_given=None,
            viewed=False)
        EventModel.from_event(ev).save()
        ev2 = EventModel.objects.get(answer=self.ANSWER).to_event()

        self.assertIsInstance(ev, NoAchievementsEvent,
                              'Event is of a wrong type')
        self.assertEqual(ev, ev2, 'Event was not saved and restored fine')

    def test_level_given_ok(self):
        ev = Event.build(
            timestamp=self.TIMESTAMP,
            user=self.USER,
            answer=self.ANSWER,
            points_given=10,
            coins=10,
            achievements=[],
            acceptor_fund=None,
            level_given=2,
            viewed=False)
        EventModel.from_event(ev).save()
        ev2 = EventModel.objects.get(answer=self.ANSWER).to_event()

        self.assertIsInstance(ev, LevelEvent, 'Event is of a wrong type')
        self.assertEqual(ev, ev2, 'Event was not saved and restored fine')

    def test_badge_given_ok(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        RuleModel.from_rule(rule).save()
        ev = Event.build(
            timestamp=self.TIMESTAMP,
            user=self.USER,
            answer=self.ANSWER,
            points_given=10,
            coins=10,
            achievements=[rule],
            acceptor_fund=None,
            level_given=None,
            viewed=False)
        EventModel.from_event(ev).save()
        ev2 = EventModel.objects.get(answer=self.ANSWER).to_event()

        self.assertIsInstance(ev, AchievementsEvent,
                              'Event is of a wrong type')
        self.assertEqual(ev, ev2, 'Event was not saved and restored fine')

    def test_level_badge_given_ok(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        RuleModel.from_rule(rule).save()
        ev = Event.build(
            timestamp=self.TIMESTAMP,
            user=self.USER,
            answer=self.ANSWER,
            points_given=10,
            coins=10,
            achievements=[rule],
            acceptor_fund=None,
            level_given=2,
            viewed=False)
        EventModel.from_event(ev).save()
        ev2 = EventModel.objects.get(answer=self.ANSWER).to_event()

        self.assertIsInstance(ev, AchievementsLevelEvent,
                              'Event is of a wrong type')
        self.assertEqual(ev, ev2, 'Event was not saved and restored fine')

    def test_donate_ok(self):
        with TemporaryFile('w+b', suffix='.jpg') as f:
            load = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAbElEQVR' \
                   b'4nO3Q0QmAMBAFwWitKSvFWsOKECIz/8c7dgwAAAAAAAAAAAAAADjHtW' \
                   b'15zve3a333R3BvWT2UWIFYgViBWIFYgViBWIFYgViBWIFYgViBWIFYg' \
                   b'ViBWIFYgVgAAAAAAAAAAAAAAPBTD1i3AiiQSFCiAAAAAElFTkSuQmCC'
            f.write(base64.b64decode(load))

            fund = Fund(
                fund_id='newfund',
                name='New fund',
                description='description',
                site='site.com',
                email='email@email.ek',
                logo=f,
                donatable=True)
            fm = FundModel.from_fund(fund).save()
            ev = Event.build(
                timestamp=self.TIMESTAMP,
                user=self.USER,
                answer=None,
                points_given=0,
                coins=-10,
                achievements=[],
                acceptor_fund=fund,
                level_given=None,
                viewed=True)
            EventModel.from_event(ev).save()
            ev2 = EventModel.objects.get(
                user=self.USER,
                acceptor_fund=fm
            ).to_event()

            self.assertIsInstance(ev, DonateEvent, 'Event is of a wrong type')
            self.assertEqual(ev, ev2, 'Event was not saved and restored fine')
