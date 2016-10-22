#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_task_types
"""
import unittest
from unittest.mock import patch, Mock

from vulyk.models.exc import TaskImportError, TaskNotFoundError
from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractTask, AbstractAnswer

from .base import (
    _collection,
    BaseTest,
    mocked_get_connection,
)
from .fixtures import FakeType


class TestTaskTypes(BaseTest):
    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def tearDown(self):
        _collection.tasks.drop()

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

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    @patch('mongoengine.queryset.base.BaseQuerySet.count', lambda *a: 22)
    def test_to_dict(self):
        got = {
            'name': 'Fake name',
            'description': 'Fake description',
            'type': 'FakeTaskType',
            'tasks': 22
        }

        self.assertDictEqual(FakeType({}).to_dict(), got)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_import_tasks(self):
        tasks = [{'name': '1'}, {'name': '2'}, {'name': '3'}]
        repo = FakeType({})

        repo.import_tasks(tasks, 'default')

        self.assertEqual(_collection.tasks.count(), len(tasks))
        self.assertEqual(repo.task_model.objects.count(), 3)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_import_tasks_not_dict(self):
        tasks = [{'name': '1'}, tuple(), {'name': '3'}]

        self.assertRaises(TaskImportError,
                          lambda: FakeType({}).import_tasks(tasks, 'default'))

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_import_tasks_not_list(self):
        self.assertRaises(TaskImportError,
                          lambda: FakeType({}).import_tasks(
                              {'name': '1'},
                              'default'))

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_import_fails_when_overwriting(self):
        tasks = [{'name': '0'}, {'name': '1'}, {'name': '1'}, {'name': '2'}]
        repo = FakeType({})

        self.assertRaises(TaskImportError,
                          lambda: repo.import_tasks(tasks, 'default'))
        self.assertEqual(repo.task_model.objects.count(), 2)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_skip_raises_not_found(self):
        self.assertRaises(TaskNotFoundError,
                          lambda: FakeType({}).skip_task('fake_id', {}))

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_on_done_raises_not_found(self):
        self.assertRaises(TaskNotFoundError,
                          lambda: FakeType({}).on_task_done({}, 'fake_id', {}))


if __name__ == '__main__':
    unittest.main()
