#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_task_types
"""
from datetime import datetime

from bson import ObjectId
import unittest
from unittest.mock import patch, Mock

from vulyk.ext.leaderboard import LeaderBoardManager
from vulyk.models.exc import TaskImportError, TaskNotFoundError
from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractTask, AbstractAnswer, Batch
from vulyk.models.user import User, Group

from .base import (
    BaseTest,
    DBTestHelpers
)
from .fixtures import FakeType


class TestTaskTypes(BaseTest):
    TASK_TYPE = 'test'

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def tearDown(self):
        super().tearDown()
        DBTestHelpers.collections.batches.drop()
        DBTestHelpers.collections.tasks.drop()
        DBTestHelpers.collections.reports.drop()
        DBTestHelpers.collections.groups.drop()
        DBTestHelpers.collections.users.drop()

    def test_init_task_inheritance(self):
        class NoTask(AbstractTaskType):
            task_model = Mock

        self.assertRaises(AssertionError, lambda: NoTask({}))

    def test_init_answer_inheritance(self):
        class NoAnswer(AbstractTaskType):
            task_model = AbstractTask
            answer_model = Mock

        self.assertRaises(AssertionError, lambda: NoAnswer({}))

    def test_init_type_name(self):
        class NoTypeName(AbstractTaskType):
            task_model = AbstractTask
            answer_model = AbstractAnswer

        self.assertRaises(AssertionError, lambda: NoTypeName({}))

    def test_init_template_name(self):
        class NoTemplateName(AbstractTaskType):
            task_model = AbstractTask
            answer_model = AbstractAnswer
            type_name = 'FakeTaskType'

        self.assertRaises(AssertionError, lambda: NoTemplateName({}))

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    @patch('mongoengine.queryset.base.BaseQuerySet.count', lambda *a: 22)
    def test_to_dict(self):
        got = {
            'name': 'Fake name',
            'description': 'Fake description',
            'type': 'FakeTaskType',
            'tasks': 22
        }

        self.assertDictEqual(FakeType({}).to_dict(), got)

    # region Import tasks
    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_import_tasks(self):
        tasks = ({'name': '1'}, {'name': '2'}, {'name': '3'})
        repo = FakeType({})

        repo.import_tasks(tasks, 'default')

        self.assertEqual(DBTestHelpers.collections.tasks.count(), len(tasks))
        self.assertEqual(repo.task_model.objects.count(), len(tasks))

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_import_tasks_not_dict(self):
        tasks = [{'name': '1'}, tuple(), {'name': '3'}]

        self.assertRaises(TaskImportError,
                          lambda: FakeType({}).import_tasks(tasks, 'default'))

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_import_tasks_not_list(self):
        self.assertRaises(TaskImportError,
                          lambda: FakeType({}).import_tasks(
                              {'name': '1'},
                              'default'))

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_import_fails_when_overwriting(self):
        tasks = [{'name': '0'}, {'name': '1'}, {'name': '1'}, {'name': '2'}]
        repo = FakeType({})

        self.assertRaises(TaskImportError,
                          lambda: repo.import_tasks(tasks, 'default'))
        self.assertEqual(repo.task_model.objects.count(), 2)
    # endregion Import tasks

    # region Export reports
    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_export_reports_normal(self):
        reports = []
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=2,
                      tasks_processed=0).save()
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=True,
                users_count=2,
                users_processed=[user],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(),
                task_type=task_type.type_name,
                result={}
            ).save()
            reports.append(report.as_dict())

        self.assertCountEqual(task_type.export_reports(batch=batch),
                              reports)

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_export_reports_batch(self):
        reports = []
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        batches = [
            Batch(id='batch%i' % i,
                  task_type=task_type.type_name,
                  tasks_count=1,
                  tasks_processed=0).save()
            for i in range(2)
        ]
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batches[i],
                closed=True,
                users_count=2,
                users_processed=[user],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(),
                task_type=task_type.type_name,
                result={}
            ).save()
            reports.append(report.as_dict())

        self.assertCountEqual(task_type.export_reports(batch=batches[1]),
                              reports[1:])

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_export_reports_batch_with_no_closed(self):
        """
        The case when we export the batch where no task is closed.
        Yield must be empty.
        """
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        batches = [
            Batch(id='batch%i' % i,
                  task_type=task_type.type_name,
                  tasks_count=1,
                  tasks_processed=0).save()
            for i in range(2)
        ]
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batches[i],
                closed=not bool(i),
                users_count=2,
                users_processed=[user],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]
        for i in range(len(tasks)):
            task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(),
                task_type=task_type.type_name,
                result={}
            ).save()

        self.assertCountEqual(task_type.export_reports(batch=batches[1]), [])

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_export_reports_one_is_closed(self):
        reports = []
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=2,
                      tasks_processed=0).save()
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=bool(i),
                users_count=2,
                users_processed=[user],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(),
                task_type=task_type.type_name,
                result={}
            ).save()
            reports.append(report.as_dict())

        self.assertCountEqual(task_type.export_reports(batch=batch),
                              reports[1:])

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_export_all_reports(self):
        reports = []
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=2,
                      tasks_processed=0).save()
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=bool(i),
                users_count=2,
                users_processed=[user],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(),
                task_type=task_type.type_name,
                result={}
            ).save()
            reports.append(report.as_dict())

        self.assertCountEqual(
            task_type.export_reports(batch=batch, closed=False),
            reports)

    # endregion Export reports

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_skip_raises_not_found(self):
        self.assertRaises(TaskNotFoundError,
                          lambda: FakeType({}).skip_task('fake_id', {}))

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_on_done_raises_not_found(self):
        self.assertRaises(TaskNotFoundError,
                          lambda: FakeType({}).on_task_done({}, 'fake_id', {}))

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_proxy_leaderboard_get_leaders(self):
        fake_type = FakeType({})
        fake_manager = Mock(spec=LeaderBoardManager)
        answer = [(ObjectId(), 15), (ObjectId, 2)]
        fake_manager.get_leaders = lambda: answer
        fake_type._leaderboard_manager = fake_manager

        self.assertEqual(fake_type.get_leaders(), answer,
                         'AbstractTaskType should not change leaders list')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_proxy_leaderboard_get_leaderboard(self):
        fake_type = FakeType({})
        fake_manager = Mock(spec=LeaderBoardManager)
        answer = [
            {'username': 'user1', 'freq': 12},
            {'username': 'user2', 'freq': 10}
        ]
        fake_manager.get_leaderboard = lambda limit: answer
        fake_type._leaderboard_manager = fake_manager

        self.assertEqual(fake_type.get_leaderboard(), answer,
                         'AbstractTaskType should not change leaderboard')


if __name__ == '__main__':
    unittest.main()
