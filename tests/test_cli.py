#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import gzip
import unittest

import bz2file
import click

from vulyk.cli import admin, batches, db
from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import Batch, AbstractAnswer, AbstractTask
from vulyk.models.user import Group, User

from .base import BaseTest
from .fixtures import FakeType


class TestAdmin(BaseTest):

    @classmethod
    def setUpClass(cls):
        Group(id='default',
              description='test',
              allowed_types=[FakeType.type_name]).save()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        Group.objects.delete()

        super().tearDownClass()

    def setUp(self):
        super().setUp()

        for i in range(1, 4):
            User(username='1',
                 email='%s@email.com' % i,
                 admin=i % 3 == 0).save()

    def tearDown(self):
        User.objects.delete()

        super().tearDown()

    def test_toggle_admin(self):
        admin.toggle_admin('1@email.com', False)
        admin.toggle_admin('2@email.com', True)
        admin.toggle_admin('3@email.com', True)

        self.assertFalse(
            User.objects.get(email='1@email.com').admin
        )
        self.assertTrue(
            User.objects.get(email='2@email.com').admin
        )
        self.assertTrue(
            User.objects.get(email='3@email.com').admin
        )


class TestDB(BaseTest):
    def test_open_anything(self):
        filename = 'test.bz2'
        self.assertEqual(db.open_anything(filename), bz2file.BZ2File)
        filename = 'test.gz'
        self.assertEqual(db.open_anything(filename), gzip.open)


class TestBatches(BaseTest):
    TASK_TYPE_NAME = 'declaration_task'

    class TestTaskType(AbstractTaskType):
        answer_model = AbstractAnswer
        task_model = AbstractTask
        type_name = 'declaration_task'
        template = 'some_template'
        _task_type_meta = {
            "foo": "bar",
            "int": 1,
            "float": 0.1,
            "bool1": False,
            "bool2": True,
        }

    class AnotherTaskType(TestTaskType):
        type_name = 'wrong_task'

    DEFAULT_BATCH = 'default'
    TASK_TYPE = TestTaskType({})
    WRONG_TASK_TYPE = AnotherTaskType({})

    def tearDown(self):
        Batch.objects.delete()

        super().tearDown()

    def test_add_default_batch(self):
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)
        self.assertEqual(
            batch.batch_meta,
            {
                'foo': 'bar', 'int': 1, 'float': 0.1,
                'bool1': False, 'bool2': True,
            }
        )

    def test_override_meta_information(self):
        batches.add_batch(
            self.DEFAULT_BATCH, 10, self.TASK_TYPE,
            self.DEFAULT_BATCH,
            batch_meta={
                'foo': 'barbaz', 'bool1': 'true', 'bool2': 'false'
            })

        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)
        self.assertEqual(
            batch.batch_meta,
            {
                "foo": "barbaz", "int": 1, "float": 0.1,
                "bool1": True, "bool2": False
            }
        )

    def test_broken_meta1(self):
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(
                self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                self.DEFAULT_BATCH,
                batch_meta={"newshit": "justempty"}
            )
        )

    def test_broken_meta2(self):
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(
                self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                self.DEFAULT_BATCH,
                batch_meta={"int": "simplywrong"}
            )
        )

    def test_add_new_tasks_to_default(self):
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batches.add_batch(self.DEFAULT_BATCH, 20, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 30)

    def test_add_wrong_task_type(self):
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(self.DEFAULT_BATCH,
                                      20,
                                      self.WRONG_TASK_TYPE,
                                      self.DEFAULT_BATCH))

    def test_add_second_batch(self):
        batch_name = 'new_batch'
        batches.add_batch(batch_name, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=batch_name)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)
        self.assertEqual(
            batch.batch_meta,
            {
                'foo': 'bar', 'int': 1, 'float': 0.1,
                'bool1': False, 'bool2': True
            }
        )

    def test_extend_not_default_batch(self):
        batch_name = 'new_batch'
        batches.add_batch(batch_name, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(batch_name, 20, self.TASK_TYPE,
                                      self.DEFAULT_BATCH))

    def test_validate_batch(self):
        not_exists = '4'
        batches.add_batch('1', 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch('2', 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch('3', 10, self.TASK_TYPE, self.DEFAULT_BATCH)

        self.assertEqual(
            not_exists,
            batches.validate_batch(None, None, not_exists,
                                   self.DEFAULT_BATCH))

    def test_validate_batch_exists(self):
        exists = '3'
        batches.add_batch('1', 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch('2', 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch(exists, 10, self.TASK_TYPE, self.DEFAULT_BATCH)

        self.assertRaises(
            click.BadParameter,
            lambda: batches.validate_batch(None, None, exists,
                                           self.DEFAULT_BATCH))


if __name__ == '__main__':
    unittest.main()
