# -*- coding: utf-8 -*-
"""
"""
from datetime import datetime
from decimal import Decimal
from vulyk.models.exc import TaskValidationError
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractTask, AbstractAnswer, Batch
from vulyk.models.user import User, Group
from vulyk.blueprints.gamification.models.task_types import POINTS_PER_TASK_KEY, COINS_PER_TASK_KEY
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.app import TASKS_TYPES

from .fixtures import FakeType
from ..fixtures import FakeType as BaseFakeType
from ..base import BaseTest


class TestAllocationOfMoneyAndPoints(BaseTest):
    TIMESTAMP = datetime.now()

    def setUp(self):
        super().setUp()

        TASKS_TYPES = []
        Group.objects.create(
            description='test', id='default', allowed_types=[
                FakeType.type_name, BaseFakeType.type_name
            ])

    def tearDown(self):
        User.objects.delete()
        Group.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        WorkSession.objects.delete()
        Batch.objects.delete()
        UserStateModel.objects.delete()
        EventModel.objects.delete()

        TASKS_TYPES = []
        super().tearDown()

    def test_single_allocation(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        user = User(username='user0', email='user0@email.com').save()
        batch = Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 1.0,
                COINS_PER_TASK_KEY: 1.0
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

        task_type._work_session_manager.start_work_session(task, user.id)
        task_type.on_task_done(user, task.id, {'result': 'result'})

        state = UserStateModel.objects.get(user=user)
        self.assertEqual(state.points, Decimal("1.0"))
        self.assertEqual(state.actual_coins, Decimal("1.0"))

        events = EventModel.objects.filter(user=user)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.points_given, Decimal("1.0"))
        self.assertEqual(ev.coins, Decimal("1.0"))
        self.assertEqual(ev.achievements, [])
        self.assertEqual(ev.level_given, None)
        self.assertEqual(ev.viewed, False)

        self.assertEqual(ev.timestamp, state.last_changed)

    def test_double_allocation(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        user = User(username='user0', email='user0@email.com').save()
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

        task_type._work_session_manager.start_work_session(task1, user.id)
        task_type.on_task_done(user, task1.id, {'result': 'result'})
        task_type._work_session_manager.start_work_session(task2, user.id)
        task_type.on_task_done(user, task2.id, {'result': 'result'})

        state = UserStateModel.objects.get(user=user)
        self.assertEqual(state.points, Decimal("5.0"))
        self.assertEqual(state.actual_coins, Decimal("3.0"))

        events = EventModel.objects.filter(user=user).order_by("-timestamp")
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

        user = User(username='user0', email='user0@email.com').save()
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

        task_type._work_session_manager.start_work_session(task, user.id)
        self.assertRaises(
            TaskValidationError,
            lambda: task_type.on_task_done(user, task.id, {'result': 'result'})
        )

    def test_double_allocation_different_batches(self):
        task_type = FakeType({})
        TASKS_TYPES[task_type.type_name] = task_type

        user = User(username='user0', email='user0@email.com').save()
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

        task_type._work_session_manager.start_work_session(task1, user.id)
        task_type.on_task_done(user, task1.id, {'result': 'result'})
        task_type._work_session_manager.start_work_session(task2, user.id)
        task_type.on_task_done(user, task2.id, {'result': 'result'})

        state = UserStateModel.objects.get(user=user)
        self.assertEqual(state.points, Decimal("27.5"))
        self.assertEqual(state.actual_coins, Decimal("16.5"))

        events = EventModel.objects.filter(user=user).order_by("-timestamp")
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

        user = User(username='user0', email='user0@email.com').save()
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

        task_type._work_session_manager.start_work_session(task, user.id)
        task_type.on_task_done(user, task.id, {'result': 'result'})

        self.assertEqual(UserStateModel.objects.filter(user=user).count(), 0)
        self.assertEqual(EventModel.objects.filter(user=user).count(), 0)

    def test_double_allocation_mixed_project(self):
        task_type_base = BaseFakeType({})
        task_type_new = FakeType({})
        TASKS_TYPES[task_type_base.type_name] = task_type_base
        TASKS_TYPES[task_type_new.type_name] = task_type_new

        user = User(username='user0', email='user0@email.com').save()
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

        task_type_base._work_session_manager.start_work_session(task1, user.id)
        task_type_base.on_task_done(user, task1.id, {'result': 'result'})
        task_type_new._work_session_manager.start_work_session(task2, user.id)
        task_type_new.on_task_done(user, task2.id, {'result': 'result'})

        state = UserStateModel.objects.get(user=user)
        self.assertEqual(state.points, Decimal("25"))
        self.assertEqual(state.actual_coins, Decimal("15"))

        events = EventModel.objects.filter(user=user)
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev.points_given, Decimal("25"))
        self.assertEqual(ev.coins, Decimal("15"))
        self.assertEqual(ev.achievements, [])
        self.assertEqual(ev.level_given, None)
        self.assertEqual(ev.viewed, False)

        self.assertEqual(ev.timestamp, state.last_changed)
