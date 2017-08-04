#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_worksessions
"""
from datetime import datetime, timedelta

from unittest.mock import patch

from vulyk.models.exc import (
    TaskNotFoundError,
    WorkSessionUpdateError)
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractTask, AbstractAnswer
from vulyk.models.user import User, Group

from .base import BaseTest
from .fixtures import FakeType


class TestTaskTypes(BaseTest):
    TASK_TYPE = FakeType.type_name

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])

    def tearDown(self):
        User.objects.delete()
        Group.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        WorkSession.objects.delete()

        super().tearDown()

    # region Creation
    def test_on_create_ok(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()
        task_type.work_session_manager.start_work_session(task, user.id)

        ws = task_type.work_session_manager.work_session.objects.get(
            user=user,
            task=task)

        self.assertEqual(ws.task, task)
        self.assertEqual(ws.task_type, task_type.type_name)
        self.assertEqual(ws.task_type, task.task_type)
        self.assertEqual(ws.user, user)

    def test_on_create_twice(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        fake_datetime = datetime.now() - timedelta(days=5)

        with patch('vulyk.ext.worksession.datetime') as mock_date:
            mock_date.now = lambda: fake_datetime
            task_type.work_session_manager.start_work_session(task, user.id)

        ws_first = task_type.work_session_manager.work_session.objects.get(
            user=user,
            task=task)
        # re-create later
        task_type.work_session_manager.start_work_session(task, user.id)

        ws_second = task_type.work_session_manager.work_session.objects.get(
            user=user,
            task=task)

        self.assertEqual(ws_first.id, ws_second.id)
        self.assertEqual((ws_second.start_time - ws_first.start_time).days, 5)
    # endregion Creation

    # region Record activity
    def test_update_session_normal(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch='any_batch',
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()
        duration = 50
        fake_datetime = datetime.now() - timedelta(seconds=70)

        with patch('vulyk.ext.worksession.datetime') as mock_date:
            mock_date.now = lambda: fake_datetime
            task_type.work_session_manager.start_work_session(task, user.id)

        task_type.record_activity(user.id, task.id, duration)

        session = WorkSession.objects.get(user=user.id, task=task)

        self.assertEqual(session.activity, duration)

    def test_update_session_twice(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch='any_batch',
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()
        duration = 50
        fake_datetime = datetime.now() - timedelta(seconds=110)

        with patch('vulyk.ext.worksession.datetime') as mock_date:
            mock_date.now = lambda: fake_datetime
            task_type.work_session_manager.start_work_session(task, user.id)

        task_type.record_activity(user.id, task.id, duration)
        task_type.record_activity(user.id, task.id, duration)

        session = WorkSession.objects.get(user=user.id, task=task)

        self.assertEqual(session.activity, duration * 2)

    def test_update_session_overdrive(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch='any_batch',
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()
        duration = 50
        fake_datetime = datetime.now() - timedelta(seconds=30)

        with patch('vulyk.ext.worksession.datetime') as mock_date:
            mock_date.now = lambda: fake_datetime
            task_type.work_session_manager.start_work_session(task, user.id)

        self.assertRaises(
            WorkSessionUpdateError,
            lambda: task_type.record_activity(user.id, task.id, duration)
        )

        session = WorkSession.objects.get(user=user.id, task=task)

        self.assertEqual(session.activity, 0)

    def test_update_session_negative(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch='any_batch',
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()
        duration = -50
        fake_datetime = datetime.now() - timedelta(seconds=30)

        with patch('vulyk.ext.worksession.datetime') as mock_date:
            mock_date.now = lambda: fake_datetime
            task_type.work_session_manager.start_work_session(task, user.id)

        self.assertRaises(
            WorkSessionUpdateError,
            lambda: task_type.record_activity(user.id, task.id, duration)
        )

        session = WorkSession.objects.get(user=user.id, task=task)

        self.assertEqual(session.activity, 0)

    def test_update_session_not_found(self):
        fake_type = FakeType({})
        self.assertRaises(TaskNotFoundError,
                          lambda: fake_type.record_activity('fake_id', '', 0))
    # endregion Record activity

    # region On task done
    def test_on_done_ok(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type.work_session_manager.start_work_session(task, user.id)
        task_type.on_task_done(user, task.id, {'result': 'result'})

        ws = task_type.work_session_manager.work_session.objects.get(
            user=user,
            task=task)
        answer = task_type.answer_model.objects.get(created_by=user, task=task)

        self.assertEqual(ws.answer, answer)
        self.assertLess(ws.end_time - datetime.now(), timedelta(seconds=1))
    # endregion On task done

    # region Stats
    def test_total_time_approximate(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        tasks = [
            task_type.task_model(
                id='task0',
                task_type=task_type.type_name,
                batch=None,
                closed=False,
                users_count=0,
                users_processed=[],
                users_skipped=[],
                task_data={'data': 'data'}).save(),
            task_type.task_model(
                id='task1',
                task_type=task_type.type_name,
                batch=None,
                closed=False,
                users_count=0,
                users_processed=[],
                users_skipped=[],
                task_data={'data': 'data'}).save(),
        ]

        for i, task in enumerate(tasks):
            fake_datetime = datetime.now() - timedelta(seconds=30 * (i + 1))

            with patch('vulyk.ext.worksession.datetime') as mock_date:
                mock_date.now = lambda: fake_datetime
                task_type.work_session_manager.start_work_session(
                    task,
                    user.id)

            task_type.on_task_done(user, task.id, {'result': 'result'})

        ws = task_type.work_session_manager.work_session

        self.assertEqual(
            ws.get_total_user_time_approximate(user.id),
            90
        )

    def test_total_time_precise(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        tasks = [
            task_type.task_model(
                id='task0',
                task_type=task_type.type_name,
                batch=None,
                closed=False,
                users_count=0,
                users_processed=[],
                users_skipped=[],
                task_data={'data': 'data'}).save(),
            task_type.task_model(
                id='task1',
                task_type=task_type.type_name,
                batch=None,
                closed=False,
                users_count=0,
                users_processed=[],
                users_skipped=[],
                task_data={'data': 'data'}).save(),
        ]

        for i, task in enumerate(tasks):
            fake_datetime = datetime.now() - timedelta(seconds=100 * (i + 1))

            with patch('vulyk.ext.worksession.datetime') as mock_date:
                mock_date.now = lambda: fake_datetime
                task_type.work_session_manager.start_work_session(
                    task,
                    user.id)

            task_type.record_activity(user.id, task.id, 50 * (i + 1))
            task_type.on_task_done(user, task.id, {'result': 'result'})

        ws = task_type.work_session_manager.work_session

        self.assertEqual(
            ws.get_total_user_time_precise(user.id),
            150
        )
    # endregion Stats
