#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import bz2file
import click
import gzip
import unittest

from unittest.mock import patch

from vulyk import settings
from vulyk.cli import admin, batches, db
from vulyk.models.tasks import Batch

from .base import (
    _collection,
    BaseTest,
    mocked_get_connection,
)


class TestAdmin(BaseTest):
    user_collection = _collection.user
    group_collection = _collection.groups

    def setUp(self):
        super().setUp()

        self.users = [
            dict(username='1', email='1@email.com', admin=True),
            dict(username='2', email='2@email.com', admin=True),
            dict(username='3', email='3@email.com', admin=False),
        ]
        for obj in self.users:
            obj['_id'] = self.user_collection.insert_one(obj)

        self.groups = [
            dict(description='test', _id='default', allowed_types=['test'])
        ]
        for obj in self.groups:
            obj['_id'] = self.group_collection.insert_one(obj)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_toggle_admin(self):
        admin.toggle_admin('1@email.com', False)
        admin.toggle_admin('2@email.com', True)
        admin.toggle_admin('3@email.com', True)

        self.assertFalse(
            self.user_collection.find_one({'email': '1@email.com'})['admin']
        )
        self.assertTrue(
            self.user_collection.find_one({'email': '2@email.com'})['admin']
        )
        self.assertTrue(
            self.user_collection.find_one({'email': '3@email.com'})['admin']
        )

    def tearDown(self):
        self.user_collection.drop()
        self.group_collection.drop()


class TestDB(BaseTest):
    def test_open_anything(self):
        filename = 'test.bz2'
        self.assertEqual(db.open_anything(filename), bz2file.BZ2File)
        filename = 'test.gz'
        self.assertEqual(db.open_anything(filename), gzip.open)


class TestBatches(BaseTest):
    batch_collection = _collection.batches
    DEFAULT_BATCH = settings.DEFAULT_BATCH
    TASK_TYPE = 'declaration_task'

    def tearDown(self):
        self.batch_collection.drop()

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_add_default_batch(self):
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_add_new_tasks_to_default(self):
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batches.add_batch(self.DEFAULT_BATCH, 20, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE)
        self.assertEqual(batch.tasks_count, 30)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_add_wrong_task_type(self):
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        self.assertRaises(
            click.BadParameter,
            lambda: batches.add_batch(self.DEFAULT_BATCH,
                                      20,
                                      'new_task',
                                      self.DEFAULT_BATCH))

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_add_second_batch(self):
        batch_name = 'new_batch'
        batches.add_batch(batch_name, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=batch_name)

        self.assertEqual(batch.task_type, self.TASK_TYPE)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_extend_not_default_batch(self):
        batch_name = 'new_batch'
        batches.add_batch(batch_name, 10, self.TASK_TYPE,
                          self.DEFAULT_BATCH)
        self.assertRaises(
            click.BadParameter,
            lambda: batches.add_batch(batch_name, 20, self.TASK_TYPE,
                                      self.DEFAULT_BATCH))

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_validate_batch(self):
        not_exists = '4'
        batches.add_batch('1', 10, 'declaration_task', self.DEFAULT_BATCH)
        batches.add_batch('2', 10, 'declaration_task', self.DEFAULT_BATCH)
        batches.add_batch('3', 10, 'declaration_task', self.DEFAULT_BATCH)

        self.assertEqual(
            not_exists,
            batches.validate_batch(None, None, not_exists,
                                   self.DEFAULT_BATCH))

    def test_validate_batch_exists(self):
        exists = '3'
        batches.add_batch('1', 10, 'declaration_task', self.DEFAULT_BATCH)
        batches.add_batch('2', 10, 'declaration_task', self.DEFAULT_BATCH)
        batches.add_batch(exists, 10, 'declaration_task', self.DEFAULT_BATCH)

        self.assertRaises(
            click.BadParameter,
            lambda: batches.validate_batch(None, None, exists,
                                           self.DEFAULT_BATCH))


if __name__ == '__main__':
    unittest.main()
