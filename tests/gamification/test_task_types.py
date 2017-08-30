#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_task_types
"""

import unittest
from unittest.mock import patch

from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractTask, AbstractAnswer, Batch
from vulyk.models.user import User, Group

from vulyk.blueprints.gamification.models.task_types import (
    POINTS_PER_TASK_KEY, COINS_PER_TASK_KEY, IMPORTANT_KEY
)

from ..base import BaseTest
from .fixtures import FakeType



class TestTaskTypes(BaseTest):
    TASK_TYPE = FakeType.type_name

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            description='test', id='default', allowed_types=[cls.TASK_TYPE])

    @classmethod
    def tearDownClass(cls):
        Group.objects.delete()

        super().tearDownClass()

    def tearDown(self):
        User.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        Batch.objects.delete()
        WorkSession.objects.delete()

        super().tearDown()

    # region Task type
    @patch('mongoengine.queryset.base.BaseQuerySet.count', lambda *a: 22)
    def test_to_dict_no_batch(self):
        got = {
            'name': 'Fake name',
            'description': 'Fake description',
            'type': 'FakeGamifiedTaskType',
            'tasks': 22,
            'open_tasks': 22,
            'batch_info': None,
            'has_tasks': False
        }

        self.assertDictEqual(FakeType({}).to_dict(), got)

    @patch('mongoengine.queryset.base.BaseQuerySet.count', lambda *a: 33)
    def test_to_dict_one_batch(self):
        got = {
            'name': 'Fake name',
            'description': 'Fake description',
            'type': 'FakeGamifiedTaskType',
            'tasks': 33,
            'open_tasks': 33,
            'batch_info': {
                POINTS_PER_TASK_KEY: 5.0,
                COINS_PER_TASK_KEY: 3.0,
                IMPORTANT_KEY: True,
            },
            'has_tasks': True
        }

        task_type = FakeType({})
        Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=2,
            tasks_processed=0,
            batch_meta={
                POINTS_PER_TASK_KEY: 5.0,
                COINS_PER_TASK_KEY: 3.0,
                IMPORTANT_KEY: True,
            }
        ).save()

        self.assertDictEqual(task_type.to_dict(), got)

    @patch('mongoengine.queryset.base.BaseQuerySet.count', lambda *a: 33)
    def test_to_dict_one_batch_but_closed(self):
        got = {
            'name': 'Fake name',
            'description': 'Fake description',
            'type': 'FakeGamifiedTaskType',
            'tasks': 33,
            'open_tasks': 33,
            'batch_info': None,
            'has_tasks': False
        }

        task_type = FakeType({})
        Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=2,
            tasks_processed=2,
            closed=True,
            batch_meta={
                POINTS_PER_TASK_KEY: 5.0,
                COINS_PER_TASK_KEY: 3.0,
                IMPORTANT_KEY: True,
            }
        ).save()

        self.assertDictEqual(task_type.to_dict(), got)

    @patch('mongoengine.queryset.base.BaseQuerySet.count', lambda *a: 44)
    def test_to_dict_two_batch(self):
        got = {
            'name': 'Fake name',
            'description': 'Fake description',
            'type': 'FakeGamifiedTaskType',
            'tasks': 44,
            'open_tasks': 44,
            'batch_info': {
                POINTS_PER_TASK_KEY: 15.0,
                COINS_PER_TASK_KEY: 13.0,
                IMPORTANT_KEY: True,
            },
            'has_tasks': True
        }

        task_type = FakeType({})
        Batch(
            id='default',
            task_type=task_type.type_name,
            tasks_count=2,
            tasks_processed=2,
            closed=True,
            batch_meta={
                POINTS_PER_TASK_KEY: 5.0,
                COINS_PER_TASK_KEY: 3.0,
                IMPORTANT_KEY: False,
            }
        ).save()

        Batch(
            id='zzzzz',
            task_type=task_type.type_name,
            tasks_count=10,
            tasks_processed=2,
            closed=False,
            batch_meta={
                POINTS_PER_TASK_KEY: 15.0,
                COINS_PER_TASK_KEY: 13.0,
                IMPORTANT_KEY: True,
            }
        ).save()

        self.assertDictEqual(task_type.to_dict(), got)
    # endregion Task type


if __name__ == '__main__':
    unittest.main()
