# -*- coding: utf-8 -*-
"""
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from vulyk.app import TASKS_TYPES
from vulyk.blueprints.gamification import listeners
from vulyk.blueprints.gamification.core.rules import Rule
from vulyk.blueprints.gamification.core.state import (
    UserState, InvalidUserStateException)
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.rules import (
    RuleModel, ProjectAndFreeRules)
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.models.task_types import \
    POINTS_PER_TASK_KEY, COINS_PER_TASK_KEY
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractTask, AbstractAnswer, Batch
from vulyk.models.user import User, Group

from .fixtures import FakeType
from ..base import BaseTest
from ..fixtures import FakeType as BaseFakeType


class TestAllocationOfMoneyAndPoints(BaseTest):
    TIMESTAMP = datetime.now()
    USER = None
    BATCH = None

    def setUp(self):
        super().setUp()

        TASKS_TYPES = []
        Group.objects.create(
            description='test', id='default', allowed_types=[
                FakeType.type_name, BaseFakeType.type_name
            ])
        self.USER = User(username='user0', email='user0@email.com').save()
        self.BATCH = Batch(
            id='default',
            task_type=FakeType.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 1.0,
                COINS_PER_TASK_KEY: 1.0
            }
        ).save()

    def tearDown(self):
        User.objects.delete()
        Group.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        WorkSession.objects.delete()
        Batch.objects.delete()

        UserStateModel.objects.delete()
        EventModel.objects.delete()
        RuleModel.objects.delete()

        TASKS_TYPES = []
        super().tearDown()

    def test_single_allocation(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=self.BATCH,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type._work_session_manager.start_work_session(task, self.USER.id)
        task_type.on_task_done(self.USER, task.id, {'result': 'result'})

        events = EventModel.objects.filter(user=self.USER)
        state = UserStateModel.get_or_create_by_user(user=self.USER)

        self.assertEqual(len(events), 1)
        ev = events[0].to_event()
        self.assertEqual(ev.points_given, Decimal("1.0"))
        self.assertEqual(ev.coins, Decimal("1.0"))
        self.assertEqual(ev.achievements, [])
        self.assertEqual(ev.level_given, None)
        self.assertEqual(ev.viewed, False)

        self.assertEqual(state.points, ev.points_given)
        self.assertEqual(state.actual_coins, ev.coins)
        self.assertEqual(state.potential_coins, Decimal())
        self.assertEqual(state.level, 0)
        self.assertEqual(state.achievements, {})
        self.assertEqual(ev.timestamp, state.last_changed)

    def test_single_allocation_badge_given(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=self.BATCH,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        rule = Rule(
            badge='Faithful Fury',
            name='rule_1',
            description='Kill one fly',
            bonus=0,
            tasks_number=1,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)
        RuleModel.from_rule(rule).save()

        task_type._work_session_manager.start_work_session(task, self.USER.id)
        task_type.on_task_done(self.USER, task.id, {'result': 'result'})

        events = EventModel.objects.filter(user=self.USER)
        state = UserStateModel.get_or_create_by_user(user=self.USER)

        ev = events[0].to_event()
        self.assertEqual(ev.points_given, Decimal("1.0"))
        self.assertEqual(ev.coins, Decimal("1.0"))
        self.assertEqual(ev.level_given, None)
        self.assertEqual(ev.viewed, False)
        self.assertEqual(ev.achievements, [rule])

        self.assertEqual(state.points, ev.points_given)
        self.assertEqual(state.actual_coins, ev.coins)
        self.assertEqual(state.potential_coins, Decimal())
        self.assertEqual(state.level, 0)
        self.assertEqual(ev.timestamp, state.last_changed)
        self.assertEqual(state.achievements, {rule.id: rule})

    def test_double_allocation(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        batch = Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=2,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 2.5,
                COINS_PER_TASK_KEY: 1.5
            }
        ).save()

        task1 = task_type.task_model(
            id='task1',
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task2 = task_type.task_model(
            id='task2',
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type._work_session_manager.start_work_session(task1, self.USER.id)
        task_type.on_task_done(self.USER, task1.id, {'result': 'result'})
        task_type._work_session_manager.start_work_session(task2, self.USER.id)
        task_type.on_task_done(self.USER, task2.id, {'result': 'result'})

        state = UserStateModel.get_or_create_by_user(user=self.USER)
        self.assertEqual(state.points, Decimal("5.0"))
        self.assertEqual(state.actual_coins, Decimal("3.0"))

        events = EventModel.objects \
            .filter(user=self.USER) \
            .order_by("-timestamp")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].timestamp, state.last_changed)

        for ev in events:
            self.assertEqual(ev.points_given, Decimal("2.5"))
            self.assertEqual(ev.coins, Decimal("1.5"))
            self.assertEqual(ev.achievements, [])
            self.assertEqual(ev.level_given, None)
            self.assertEqual(ev.viewed, False)

    def test_wrong_allocation(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        batch = Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: -1.0,
                COINS_PER_TASK_KEY: -1.0
            }
        ).save()

        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type._work_session_manager.start_work_session(task, self.USER.id)
        self.assertRaises(
            InvalidUserStateException,
            lambda: task_type.on_task_done(self.USER,
                                           task.id,
                                           {'result': 'result'})
        )

    def test_double_allocation_different_batches(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        batch1 = Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 2.5,
                COINS_PER_TASK_KEY: 1.5
            }
        ).save()

        batch2 = Batch(
            id='yummy',
            task_type=task_type.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 25,
                COINS_PER_TASK_KEY: 15
            }
        ).save()

        task1 = task_type.task_model(
            id='task1',
            task_type=task_type.type_name,
            batch=batch1,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task2 = task_type.task_model(
            id='task2',
            task_type=task_type.type_name,
            batch=batch2,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type._work_session_manager.start_work_session(task1, self.USER.id)
        task_type.on_task_done(self.USER, task1.id, {'result': 'result'})
        task_type._work_session_manager.start_work_session(task2, self.USER.id)
        task_type.on_task_done(self.USER, task2.id, {'result': 'result'})

        state = UserStateModel.get_or_create_by_user(user=self.USER)
        self.assertEqual(state.points, Decimal("27.5"))
        self.assertEqual(state.actual_coins, Decimal("16.5"))

        events = EventModel.objects \
            .filter(user=self.USER) \
            .order_by("-timestamp")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].timestamp, state.last_changed)

        for ev in events:
            self.assertIn(ev.points_given, [Decimal("2.5"), Decimal("25")])
            self.assertIn(ev.coins, [Decimal("1.5"), Decimal("15")])
            self.assertEqual(ev.achievements, [])
            self.assertEqual(ev.level_given, None)
            self.assertEqual(ev.viewed, False)

    def test_single_allocation_no_events(self):
        task_type = BaseFakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        batch = Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=1,
            tasks_processed=0
        ).save()

        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type._work_session_manager.start_work_session(task, self.USER.id)
        task_type.on_task_done(self.USER, task.id, {'result': 'result'})

        self.assertEqual(UserStateModel.objects(user=self.USER).count(), 0)
        self.assertEqual(EventModel.objects(user=self.USER).count(), 0)

    def test_double_allocation_mixed_project(self):
        task_type_base = BaseFakeType({})
        task_type_new = FakeType({})
        TASKS_TYPES[task_type_base.type_name] = task_type_base
        TASKS_TYPES[task_type_new.type_name] = task_type_new

        batch1 = Batch(
            id='default',
            task_type=task_type_base.type_name,
            tasks_count=1,
            tasks_processed=0
        ).save()

        batch2 = Batch(
            id='yummy',
            task_type=task_type_new.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 25,
                COINS_PER_TASK_KEY: 15
            }
        ).save()

        task1 = task_type_base.task_model(
            id='task1',
            task_type=task_type_base.type_name,
            batch=batch1,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task2 = task_type_new.task_model(
            id='task2',
            task_type=task_type_new.type_name,
            batch=batch2,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type_base._work_session_manager.start_work_session(task1,
                                                                self.USER.id)
        task_type_base.on_task_done(self.USER, task1.id, {'result': 'result'})
        task_type_new._work_session_manager.start_work_session(task2,
                                                               self.USER.id)
        task_type_new.on_task_done(self.USER, task2.id, {'result': 'result'})

        state = UserStateModel.get_or_create_by_user(user=self.USER)
        self.assertEqual(state.points, Decimal("25"))
        self.assertEqual(state.actual_coins, Decimal("15"))

        events = EventModel.objects.filter(user=self.USER)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.points_given, Decimal("25"))
        self.assertEqual(ev.coins, Decimal("15"))
        self.assertEqual(ev.achievements, [])
        self.assertEqual(ev.level_given, None)
        self.assertEqual(ev.viewed, False)

        self.assertEqual(ev.timestamp, state.last_changed)


class TestAllocationBadges(BaseTest):
    SATURDAY = datetime(2017, 7, 8)
    SUNDAY = datetime(2017, 7, 9)
    MONDAY = datetime(2017, 7, 10)
    USER = None
    GET_ACTUAL_RULES = 'vulyk.blueprints.gamification.models.rules.' \
                       'RuleModel.get_actual_rules'

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[
                FakeType.type_name, BaseFakeType.type_name
            ])
        self.USER = User(username='user0', email='user0@email.com').save()

    def tearDown(self):
        User.objects.delete()
        Group.objects.delete()

        super().tearDown()

    def test_get_rules_no_earned_no_batch_no_weekend(self):
        rookie_state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.MONDAY
        )

        def patched_rules(**kwargs):
            assert kwargs['skip_ids'] == []
            assert kwargs['rule_filter'] == ProjectAndFreeRules('')
            assert not kwargs['is_weekend']

        with patch(self.GET_ACTUAL_RULES, patched_rules):
            listeners.get_actual_rules(rookie_state, '', self.MONDAY)
            self.assertRaises(
                AssertionError,
                lambda: listeners.get_actual_rules(
                    rookie_state,
                    'batch_should_not_be_here',
                    self.MONDAY))

    def test_get_rules_badges_no_batch_no_weekend(self):
        rule = Rule(
            badge='',
            name='rule_1',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        state = UserState(
            user=self.USER,
            level=20,
            points=Decimal(5000),
            actual_coins=Decimal(3240),
            potential_coins=Decimal(4000),
            achievements=[rule],
            last_changed=self.MONDAY
        )

        def patched_rules(**kwargs):
            assert kwargs['skip_ids'] == [100]
            assert kwargs['rule_filter'] == ProjectAndFreeRules('')
            assert not kwargs['is_weekend']

        with patch(self.GET_ACTUAL_RULES, patched_rules):
            listeners.get_actual_rules(state, '', self.MONDAY)

    def test_get_rules_no_badges_no_batch_weekend(self):
        state = UserState(
            user=self.USER,
            level=20,
            points=Decimal(5000),
            actual_coins=Decimal(3240),
            potential_coins=Decimal(4000),
            achievements=[],
            last_changed=self.MONDAY
        )

        def patched_rules(**kwargs):
            assert kwargs['skip_ids'] == []
            assert kwargs['rule_filter'] == ProjectAndFreeRules('')
            assert kwargs['is_weekend']

        with patch(self.GET_ACTUAL_RULES, patched_rules):
            listeners.get_actual_rules(state, '', self.SATURDAY)
            listeners.get_actual_rules(state, '', self.SUNDAY)

    def test_get_rules_badges_batch_weekend(self):
        rule = Rule(
            badge='',
            name='rule_1',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        state = UserState(
            user=self.USER,
            level=20,
            points=Decimal(5000),
            actual_coins=Decimal(3240),
            potential_coins=Decimal(4000),
            achievements=[rule],
            last_changed=self.MONDAY
        )

        def patched_rules(**kwargs):
            assert kwargs['skip_ids'] == [100]
            assert kwargs['rule_filter'] == ProjectAndFreeRules('batch_1')
            assert kwargs['is_weekend']

        with patch(self.GET_ACTUAL_RULES, patched_rules):
            listeners.get_actual_rules(state, 'batch_1', self.SUNDAY)
