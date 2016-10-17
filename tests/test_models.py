#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_models
"""
import unittest

from unittest.mock import patch

from vulyk.models.user import User, Group

from .base import (
    _collection,
    BaseTest,
    mocked_get_connection
)


class TestUser(BaseTest):
    user_collection = _collection.user
    group_collection = _collection.groups

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=['test'])

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_add_default_group(self):
        User(username='1', email='1@email.com', admin=True).save()
        User(username='2', email='2@email.com', admin=False).save()
        User(username='3', email='3@email.com', admin=False).save()

        for u in User.objects():
            self.assertIn('default', [g.id for g in u.groups],
                          'Default group omitted!')

    def tearDown(self):
        self.user_collection.drop()
        self.group_collection.drop()


if __name__ == '__main__':
    unittest.main()
