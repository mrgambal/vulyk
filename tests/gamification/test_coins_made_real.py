# -*- coding: utf-8 -*-
"""
test_coins_made_real
"""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from vulyk.app import TASKS_TYPES
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.models.task_types import COINS_PER_TASK_KEY, POINTS_PER_TASK_KEY
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractAnswer, AbstractTask, Batch
from vulyk.models.user import Group, User

from ..base import BaseTest
from ..fixtures import FakeType as BaseFakeType
from .fixtures import FakeType


class TestCoinsMadeReal(BaseTest):
    TIMESTAMP = datetime.now(tz=timezone.utc)
    USER_ONE: User
    GAME_BATCH: Batch
    BASIC_BATCH: Batch
    TASKS_TYPES.clear()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            description="test", id="default", allowed_types=[FakeType.type_name, BaseFakeType.type_name]
        )
        cls.USER_ONE = User(username="user0", email="user0@email.com").save()
        cls.USER_TWO = User(username="user1", email="user1@email.com").save()

    @classmethod
    def tearDownClass(cls):
        User.objects.delete()
        Group.objects.delete()

        super().tearDownClass()

    def setUp(self):
        super().setUp()

        self.GAME_BATCH = Batch(
            id="gamified",
            task_type=FakeType.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={POINTS_PER_TASK_KEY: 1.0, COINS_PER_TASK_KEY: 1.0},
        ).save()
        self.BASIC_BATCH = Batch(
            id="default", task_type=BaseFakeType.type_name, tasks_count=1, tasks_processed=0
        ).save()

    def tearDown(self):
        TASKS_TYPES.clear()

        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        WorkSession.objects.delete()
        Batch.objects.delete()

        UserStateModel.objects.delete()
        EventModel.objects.delete()

        super().tearDown()

    def test_not_gamified_batch(self):
        fake_type = BaseFakeType({})
        task = fake_type.task_model(
            id="task0",
            task_type=fake_type.type_name,
            batch=self.BASIC_BATCH,
            closed=False,
            users_count=2,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        TASKS_TYPES[fake_type.type_name] = fake_type

        fake_type.work_session_manager.start_work_session(task, self.USER_ONE.id)
        fake_type.on_task_done(self.USER_ONE, task.id, {"result": "result"})
        usm = UserStateModel.get_or_create_by_user(self.USER_ONE)

        self.BASIC_BATCH.reload()

        self.assertTrue(self.BASIC_BATCH.closed)
        self.assertEqual(usm.potential_coins, Decimal(0))
        self.assertEqual(usm.actual_coins, Decimal(0))

    def test_gamified_batch_ok(self):
        fake_type = FakeType({})
        task = fake_type.task_model(
            id="task0",
            task_type=fake_type.type_name,
            batch=self.GAME_BATCH,
            closed=False,
            users_count=2,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        TASKS_TYPES[fake_type.type_name] = fake_type

        fake_type.work_session_manager.start_work_session(task, self.USER_ONE.id)
        fake_type.on_task_done(self.USER_ONE, task.id, {"result": "result"})
        usm = UserStateModel.get_or_create_by_user(self.USER_ONE)

        self.GAME_BATCH.reload()

        self.assertTrue(self.GAME_BATCH.closed)
        self.assertEqual(usm.potential_coins, Decimal(0))
        self.assertEqual(usm.actual_coins, Decimal(1))

    def test_materialize_for_all(self):
        class AnotherFakeGamifiedType(FakeType):
            type_name = "yet_another_type"

        another_type = AnotherFakeGamifiedType({})
        another_batch = Batch(
            id="gamified_new",
            task_type=another_type.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={POINTS_PER_TASK_KEY: 1.0, COINS_PER_TASK_KEY: 20.0},
        ).save()
        another_task = another_type.task_model(
            id="task0",
            task_type=another_type.type_name,
            batch=another_batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()

        fake_type = FakeType({})
        task = fake_type.task_model(
            id="task1",
            task_type=fake_type.type_name,
            batch=self.GAME_BATCH,
            closed=False,
            users_count=2,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        TASKS_TYPES[fake_type.type_name] = fake_type
        TASKS_TYPES[another_type.type_name] = another_type

        # when user finishes the task not to be closed
        another_type.work_session_manager.start_work_session(another_task, self.USER_ONE.id)
        another_type.on_task_done(self.USER_ONE, another_task.id, {"result": "result"})
        usm = UserStateModel.get_or_create_by_user(self.USER_ONE)
        # then user shall got its potential coins
        self.assertEqual(usm.potential_coins, Decimal(20))
        self.assertEqual(usm.actual_coins, Decimal())
        # when user finishes the task to be closed and to close the batch
        fake_type.work_session_manager.start_work_session(task, self.USER_ONE.id)
        fake_type.on_task_done(self.USER_ONE, task.id, {"result": "result"})
        usm = UserStateModel.get_or_create_by_user(self.USER_ONE)
        # then only the second income shall become actual
        self.assertEqual(usm.potential_coins, Decimal(20))
        self.assertEqual(usm.actual_coins, Decimal(1))

    def test_materialize_only_participated(self):
        class AnotherFakeGamifiedType(FakeType):
            type_name = "yet_another_type"

        another_type = AnotherFakeGamifiedType({})
        another_batch = Batch(
            id="gamified_new",
            task_type=another_type.type_name,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={POINTS_PER_TASK_KEY: 1.0, COINS_PER_TASK_KEY: 20.0},
        ).save()
        another_task = another_type.task_model(
            id="task0",
            task_type=another_type.type_name,
            batch=another_batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()

        fake_type = FakeType({})
        task = fake_type.task_model(
            id="task1",
            task_type=fake_type.type_name,
            batch=self.GAME_BATCH,
            closed=False,
            users_count=2,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        TASKS_TYPES[fake_type.type_name] = fake_type
        TASKS_TYPES[another_type.type_name] = another_type

        # when user one finishes the task not to be closed
        another_type.work_session_manager.start_work_session(another_task, self.USER_ONE.id)
        another_type.on_task_done(self.USER_ONE, another_task.id, {"result": "result"})
        # and user two finishes the task to be closed and to close the batch
        fake_type.work_session_manager.start_work_session(task, self.USER_TWO.id)
        fake_type.on_task_done(self.USER_TWO, task.id, {"result": "result"})
        # then only the user two shall get actual coins
        usm_one = UserStateModel.get_or_create_by_user(self.USER_ONE)
        usm_two = UserStateModel.get_or_create_by_user(self.USER_TWO)

        self.assertEqual(usm_one.potential_coins, Decimal(20))
        self.assertEqual(usm_one.actual_coins, Decimal(0))
        self.assertEqual(usm_two.potential_coins, Decimal(0))
        self.assertEqual(usm_two.actual_coins, Decimal(1))

    def test_materialize_all_participated(self):
        fake_type = FakeType({})
        task = fake_type.task_model(
            id="task1",
            task_type=fake_type.type_name,
            batch=self.GAME_BATCH,
            closed=False,
            users_count=1,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        TASKS_TYPES[fake_type.type_name] = fake_type

        # when user one finishes the task
        fake_type.work_session_manager.start_work_session(task, self.USER_ONE.id)
        fake_type.on_task_done(self.USER_ONE, task.id, {"result": "result"})
        # and user two finishes the task
        fake_type.work_session_manager.start_work_session(task, self.USER_TWO.id)
        fake_type.on_task_done(self.USER_TWO, task.id, {"result": "result"})
        # then both users shall get actual coins
        usm_one = UserStateModel.get_or_create_by_user(self.USER_ONE)
        usm_two = UserStateModel.get_or_create_by_user(self.USER_TWO)

        self.assertEqual(usm_one.potential_coins, Decimal(0))
        self.assertEqual(usm_one.actual_coins, Decimal(1))
        self.assertEqual(usm_two.potential_coins, Decimal(0))
        self.assertEqual(usm_two.actual_coins, Decimal(1))


if __name__ == "__main__":
    unittest.main()
