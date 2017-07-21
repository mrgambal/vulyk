# -*- coding: utf-8 -*-
"""
test_event_models
"""
import base64
from datetime import datetime, timedelta
from decimal import Decimal
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
            points_given=Decimal(10),
            coins=Decimal(10),
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
            points_given=Decimal(10),
            coins=Decimal(10),
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
            points_given=Decimal(10),
            coins=Decimal(10),
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
            points_given=Decimal(10),
            coins=Decimal(10),
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
                coins=Decimal(-10),
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

    def test_level_badge_to_dict(self):
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
        ev = Event.build(
            timestamp=self.TIMESTAMP,
            user=self.USER,
            answer=self.ANSWER,
            points_given=Decimal(10),
            coins=Decimal(10),
            achievements=[rule],
            acceptor_fund=None,
            level_given=2,
            viewed=False)
        expected = {
            'timestamp': self.TIMESTAMP,
            'user': self.USER.username,
            'answer': self.ANSWER.as_dict(),
            'points_given': 10,
            'coins': 10,
            'achievements': [rule.to_dict()],
            'acceptor_fund': None,
            'level_given': 2,
            'viewed': False}

        self.assertDictEqual(expected, ev.to_dict(),
                             'Event was not translated to dict correctly')

    def test_donate_to_dict(self):
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
            ev = Event.build(
                timestamp=self.TIMESTAMP,
                user=self.USER,
                answer=None,
                points_given=0,
                coins=Decimal(-10),
                achievements=[],
                acceptor_fund=fund,
                level_given=None,
                viewed=True)
            expected = {
                'timestamp': self.TIMESTAMP,
                'user': self.USER.username,
                'answer': None,
                'points_given': 0,
                'coins': -10,
                'achievements': [],
                'acceptor_fund': fund.to_dict(),
                'level_given': None,
                'viewed': True}

            self.assertDictEqual(expected, ev.to_dict(),
                                 'Event was not translated to dict correctly')

    def test_unread_events_correct_user(self):
        users = [
            User(username='user%s' % i, email='user%s@email.com' % i).save()
            for i in range(0, 3)
        ]

        for i in range(0, 9):
            user = users[i % 3]
            ev = Event.build(
                timestamp=self.TIMESTAMP + timedelta(seconds=i),
                user=users[i % 3],
                answer=FakeType.answer_model(
                    task=FakeType.task_model(
                        id='task%s' % i,
                        task_type=self.TASK_TYPE,
                        batch='default',
                        closed=False,
                        users_count=0,
                        users_processed=[],
                        task_data={'data': 'data'}).save(),
                    created_by=user,
                    created_at=datetime.now(),
                    task_type=self.TASK_TYPE,
                    result={}).save(),
                points_given=Decimal(10),
                coins=Decimal(10),
                achievements=[],
                acceptor_fund=None,
                level_given=2,
                viewed=False)
            EventModel.from_event(ev).save()
        index = 2
        events = EventModel.get_unread_events(users[index])

        self.assertEqual(
            len(events), 3,
            'Wrong number of unread events extracted')
        self.assertTrue(
            all([e.user.id == users[index].id for e in events]),
            'Unread events list contains wrong user\'s events')

    def test_unread_events_correct_sorting(self):
        users = [
            User(username='user%s' % i, email='user%s@email.com' % i).save()
            for i in range(0, 3)]

        for i in range(0, 9):
            user = users[i % 3]
            ev = Event.build(
                timestamp=self.TIMESTAMP + timedelta(seconds=i),
                user=users[i % 3],
                answer=FakeType.answer_model(
                    task=FakeType.task_model(
                        id='task%s' % i,
                        task_type=self.TASK_TYPE,
                        batch='default',
                        closed=False,
                        users_count=0,
                        users_processed=[],
                        task_data={'data': 'data'}).save(),
                    created_by=user,
                    created_at=datetime.now(),
                    task_type=self.TASK_TYPE,
                    result={}).save(),
                points_given=Decimal(10),
                coins=Decimal(10),
                achievements=[],
                acceptor_fund=None,
                level_given=2,
                viewed=False)
            EventModel.from_event(ev).save()
        index = 2
        events = EventModel.get_unread_events(users[index])

        self.assertSequenceEqual([
            self.TIMESTAMP + timedelta(seconds=index + 3 * i)
            for i in range(3)],
            [e.timestamp for e in events],
            'Unread events list has wrong sorting')

    def test_unread_events_set_viewed(self):
        users = [
            User(username='user%s' % i, email='user%s@email.com' % i).save()
            for i in range(0, 3)]

        for i in range(0, 9):
            user = users[i % 3]
            ev = Event.build(
                timestamp=self.TIMESTAMP + timedelta(seconds=i),
                user=users[i % 3],
                answer=FakeType.answer_model(
                    task=FakeType.task_model(
                        id='task%s' % i,
                        task_type=self.TASK_TYPE,
                        batch='default',
                        closed=False,
                        users_count=0,
                        users_processed=[],
                        task_data={'data': 'data'}).save(),
                    created_by=user,
                    created_at=datetime.now(),
                    task_type=self.TASK_TYPE,
                    result={}).save(),
                points_given=Decimal(10),
                coins=Decimal(10),
                achievements=[],
                acceptor_fund=None,
                level_given=2,
                viewed=False)
            EventModel.from_event(ev).save()

        for user in users:
            events = EventModel.get_unread_events(user)
            self.assertEqual(
                len(events), 3,
                '%s should have 3 unread events' % user.username)

            new_events = EventModel.get_unread_events(user)
            self.assertEqual(
                len(new_events), 0,
                'Unexpected unread events for %s.' % user.username)
