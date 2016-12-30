#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_leaderboard
"""
from datetime import datetime
import unittest

from unittest.mock import patch

from vulyk.models.tasks import Batch
from vulyk.ext.leaderboard import LeaderBoardManager
from vulyk.models.user import User, Group

from .base import (
    BaseTest,
    DBTestHelpers
)
from .fixtures import FakeType


class TestLeaderBoard(BaseTest):
    TASK_TYPE = 'test'

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_get_leaders_sorted_yield(self):
        """
        Really slow garbage. Uses PyExecJs to emulate Map-Reduce in MongoDB.
        """
        task_type = FakeType({})
        manager = LeaderBoardManager(task_type.type_name,
                                     task_type.answer_model,
                                     User)
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

        self.assertEqual(
            manager.get_leaders(),
            [(users[1].id, 4), (users[0].id, 2)]
        )

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_get_leaderboard_normal(self):
        users = [
            User(username='user%s' % i, email='user%s@email.com' % i).save()
            for i in range(3)
        ]
        leaders = [(users[i].id, i) for i in range(3)]
        task_type = FakeType({})
        manager = LeaderBoardManager(task_type.type_name,
                                     task_type.answer_model,
                                     User)
        manager.get_leaders = lambda: leaders

        self.assertEqual(
            manager.get_leaderboard(5),
            [
                {'rank': 1, 'user': users[2], 'freq': 2},
                {'rank': 2, 'user': users[1], 'freq': 1},
                {'rank': 3, 'user': users[0], 'freq': 0}
            ]
        )

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_get_leaderboard_if_same_count(self):
        users = [
            User(username='user%s' % i, email='user%s@email.com' % i).save()
            for i in range(4)
        ]
        leaders = [(users[i].id, i) for i in range(3)]
        leaders.append((users[3].id, 1))
        task_type = FakeType({})
        manager = LeaderBoardManager(task_type.type_name,
                                     task_type.answer_model,
                                     User)
        manager.get_leaders = lambda: leaders

        self.assertEqual(
            manager.get_leaderboard(5),
            [
                {'rank': 1, 'user': users[2], 'freq': 2},
                {'rank': 2, 'user': users[1], 'freq': 1},
                {'rank': 2, 'user': users[3], 'freq': 1},
                {'rank': 3, 'user': users[0], 'freq': 0}
            ]
        )

    def tearDown(self):
        super().tearDown()

        DBTestHelpers.collections.user.drop()
        DBTestHelpers.collections.groups.drop()
        DBTestHelpers.collections.reports.drop()
        DBTestHelpers.collections.tasks.drop()
        DBTestHelpers.collections.batches.drop()


if __name__ == '__main__':
    unittest.main()
