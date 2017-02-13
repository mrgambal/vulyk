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
    TASK_TYPE = FakeType.type_name

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def tearDown(self):
        DBTestHelpers.collections.batches.drop()
        DBTestHelpers.collections.tasks.drop()
        DBTestHelpers.collections.reports.drop()
        DBTestHelpers.collections.groups.drop()
        DBTestHelpers.collections.user.drop()

        super().tearDown()

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

    # region Next task
    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_batches_are_complete(self):
        task_type = FakeType({})
        Batch(id='default',
              task_type=task_type.type_name,
              tasks_count=2,
              tasks_processed=2).save()
        user = User(username='user0', email='user0@email.com').save()
        [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch='default',
                closed=True,
                users_count=0,
                users_processed=[],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]

        self.assertEqual(task_type.get_next(user), {},
                         'Should return an empty dict if all is done')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_not_return_processed(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch='default',
                closed=False,
                users_count=1,
                users_processed=[user],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]

        self.assertEqual(task_type.get_next(user), {},
                         'Should return an empty dict if user passed all tasks')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_return_proper_type(self):
        class NewFakeModel(AbstractTask):
            pass

        class NewFakeAnswer(AbstractAnswer):
            pass

        class NewFakeType(AbstractTaskType):
            task_model = NewFakeModel
            answer_model = NewFakeAnswer
            type_name = 'NewFakeTaskType'
            template = 'tmpl.html'

            _name = 'New Fake name'
            _description = 'New Fake description'

        old_task_type = FakeType({})
        task_type = NewFakeType({})

        group = Group(
            description='test',
            id='test',
            allowed_types=[self.TASK_TYPE, task_type.type_name]).save()
        user = User(
            username='user0',
            email='user0@email.com',
            groups=[group]).save()
        task_type.task_model(
            id='task1',
            task_type=task_type.type_name,
            batch='default',
            closed=False,
            users_count=0,
            users_processed=[],
            task_data={'data': 'data'}
        ).save()

        self.assertEqual(old_task_type.get_next(user), {},
                         'Should return no task of another type')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_not_show_skipped_until_nothing_else_left(self):
        task_type = FakeType({})
        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=2,
                      tasks_processed=0).save()
        user = User(username='user0', email='user0@email.com').save()
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=False,
                users_count=0,
                users_processed=[],
                users_skipped=[user][:i % 2],
                task_data={'data': 'data'}
            ).save() for i in range(2)
        ]
        # that's how we deal with randomized yield
        for _ in range(5):
            self.assertEqual(task_type.get_next(user), tasks[0].as_dict(),
                             'Should return only task that isn\'t skipped')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_return_skipped_if_none_else_left(self):
        task_type = FakeType({})
        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=1,
                      tasks_processed=0).save()
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[user],
            task_data={'data': 'data'}).save()

        self.assertEqual(task_type.get_next(user), task.as_dict(),
                         'Should return even skipped task if nothing else'
                         ' is available')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_fallback_to_any_batch(self):
        task_type = FakeType({})
        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=1,
                      tasks_processed=1).save()
        user = User(username='user0', email='user0@email.com').save()
        tasks = [task_type.task_model(
            id='task%s' % i,
            task_type=task_type.type_name,
            batch=[batch, 'default'][i],
            closed=not bool(i),
            users_count=1 - i,
            users_processed=[user][:1 - i],
            users_skipped=[],
            task_data={'data': 'data'}).save() for i in range(2)]

        for _ in range(5):
            self.assertEqual(task_type.get_next(user), tasks[1].as_dict(),
                             'Should return only task that isn\'t skipped')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_return_skipped_if_none_else_left_no_batch(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch='any_batch',
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[user],
            task_data={'data': 'data'}).save()

        self.assertEqual(task_type.get_next(user), task.as_dict(),
                         'Should return even skipped task if nothing else'
                         ' is available')
    # endregion Next task

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
