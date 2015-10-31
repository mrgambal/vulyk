#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import bz2file
import gzip
import unittest

from mock import patch

from vulyk.cli import admin, db
from .base import (
    _collection,
    BaseTest,
    mocked_get_connection,
)


class TestAdmin(BaseTest):

    def setUp(self):
        super(TestAdmin, self).setUp()

        self.user_collection = _collection.user
        self.group_collection = _collection.groups

        self.users = [
            dict(username='1', email='1@email.com', admin=True),
            dict(username='2', email='2@email.com', admin=True),
            dict(username='3', email='3@email.com', admin=False),
        ]
        for obj in self.users:
            obj['_id'] = self.user_collection.insert(obj)

        self.groups = [
            dict(description='test', _id='default', allowed_types=['test'])
        ]
        for obj in self.groups:
            obj['_id'] = self.group_collection.insert(obj)

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


class TestDB(BaseTest):

    def setUp(self):
        super(TestDB, self).setUp()

    def test_open_anything(self):
        filename = 'test.bz2'
        self.assertEqual(db.open_anything(filename), bz2file.BZ2File)
        filename = 'test.gz'
        self.assertEqual(db.open_anything(filename), gzip.open)

    def test_load_tasks(self):
        pass

    def test_export_tasks(self):
        pass


if __name__ == '__main__':
    unittest.main()
