#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""

import unittest
import mongomock

from mock import patch
from mongoengine.connection import register_connection

from vulyk.cli import admin


_collection = mongomock.Connection().db


def mocked_get_connection(alias):
    return {alias: _collection}


class TestAdmin(unittest.TestCase):

    def setUp(self):
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

        register_connection('default', name='default')

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
        pass

if __name__ == '__main__':
    unittest.main()
