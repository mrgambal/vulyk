#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_models
"""
from datetime import datetime
import unittest

from unittest.mock import patch

from vulyk.models.tasks import Batch
from vulyk.models.user import User, Group

from .base import (
    _collection,
    BaseTest,
    mocked_get_connection
)
from .fixtures import FakeType


class TestUser(BaseTest):
    TASK_TYPE = 'test'
    USERS = _collection.user
    GROUPS = _collection.groups

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_add_default_group(self):
        User(username='1', email='1@email.com', admin=True).save()
        User(username='2', email='2@email.com', admin=False).save()
        User(username='3', email='3@email.com').save()

        for u in User.objects():
            self.assertIn('default', [g.id for g in u.groups],
                          'Default group omitted!')

    def test_is_active(self):
        active = User(username='1', email='1@email.com', active=True)
        inactive = User(username='2', email='2@email.com', active=False)

        self.assertTrue(active.is_active(), 'Active user is shown as inactive')
        self.assertFalse(inactive.is_active(),
                         'Suspended user is shown as active')

    def test_is_admin(self):
        admin = User(username='1', email='1@email.com', admin=True)
        regular = User(username='2', email='2@email.com', admin=False)

        self.assertTrue(admin.is_admin(), 'Admin is shown as regular user')
        self.assertFalse(regular.is_admin(), 'Regular user is shown as admin')

    @patch('mongoengine.connection.get_connection', mocked_get_connection)
    def test_is_eligible_for(self):
        another_task_type = 'task_type_2'
        u1 = User(username='1', email='1@email.com', admin=True).save()

        self.assertTrue(u1.is_eligible_for(self.TASK_TYPE))
        self.assertFalse(u1.is_eligible_for(another_task_type))

    def test_as_dict(self):
        username = 'mutumba'
        email = 'mutumba@email.com'
        user = User(username=username, email=email)

        self.assertDictEqual(
            user.as_dict(),
            {
                'username': username,
                'email': email
            }
        )

    def test_get_stats(self):
        """
        Really slow garbage. Uses PyExecJs to emulate Map-Reduce in MongoDB.
        """
        task_type = FakeType({})
        users = [
            User(username='user%s' % i, email='user%s@email.com' % i).save()
            for i in range(2)
        ]

        batch = Batch(id='default',
                      task_type=task_type.type_name,
                      tasks_count=4,
                      tasks_processed=2).save()
        tasks = [
            task_type.task_model(
                id='task%s' % i,
                task_type=task_type.type_name,
                batch=batch,
                users_count=2,
                users_processed=users[i % 2:],
                task_data={'data': 'data'}
            ).save() for i in range(4)
        ]

        for i in range(len(tasks)):
            for u in users[i % 2:]:
                task_type.answer_model(
                    task=tasks[i],
                    created_by=u,
                    created_at=datetime.now(),
                    task_type=task_type.type_name,
                    result={}
                ).save()

        self.assertDictEqual(
            users[0].get_stats(task_type),
            {
                'total': 2,
                'position': 2
            }
        )
        self.assertDictEqual(
            users[1].get_stats(task_type),
            {
                'total': 4,
                'position': 1
            }
        )

        # a little cleaning
        _collection.reports.drop()
        _collection.tasks.drop()
        _collection.batches.drop()

    def tearDown(self):
        self.USERS.drop()
        self.GROUPS.drop()


if __name__ == '__main__':
    unittest.main()
