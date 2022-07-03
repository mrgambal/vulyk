#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_user_model
"""
import unittest

from vulyk.models.user import Group, User

from .base import BaseTest
from .fixtures import FakeType


class TestUser(BaseTest):
    TASK_TYPE = 'test'

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

        super().tearDown()

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

    def test_is_eligible_for(self):
        another_task_type = 'task_type_2'
        u1 = User(username='1', email='1@email.com', admin=True).save()
        u2 = User(username='2', email='2@email.com', admin=False).save()

        self.assertTrue(u1.is_eligible_for(self.TASK_TYPE))
        self.assertTrue(u1.is_eligible_for(another_task_type))
        self.assertTrue(u2.is_eligible_for(self.TASK_TYPE))
        self.assertFalse(u2.is_eligible_for(another_task_type))

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
        task_type = FakeType({})
        user = User(username='mutumba', email='mutumba@email.com').save()
        leaders = [(user.id, 4), ('user0', 2)]
        task_type.get_leaders = lambda: leaders

        self.assertEqual(
            user.get_stats(task_type),
            {
                'total': 4,
                'position': 1
            }
        )

    def test_get_stats_share_place_if_same_count(self):
        task_type = FakeType({})
        user = User(username='mutumba', email='mutumba@email.com').save()
        leaders = [('user0', 12), (user.id, 4), ('user1', 4)]
        task_type.get_leaders = lambda: leaders

        self.assertEqual(
            user.get_stats(task_type),
            {
                'total': 4,
                'position': 2
            }
        )

    def test_get_stats_others_share_place_if_same_count(self):
        task_type = FakeType({})
        user = User(username='mutumba', email='mutumba@email.com').save()
        leaders = [('user0', 12), ('user1', 4), ('user2', 4), (user.id, 3)]
        task_type.get_leaders = lambda: leaders

        self.assertEqual(
            user.get_stats(task_type),
            {
                'total': 3,
                'position': 3
            }
        )

    def test_get_by_id(self):
        user = User(username='mutumba', email='mutumba@email.com').save()
        uid = str(user.id)

        self.assertEqual(user, User.get_by_id(uid))

    def test_get_by_id_not_found(self):
        User(username='mutumba', email='mutumba@email.com').save()
        uid = 'mutumba'

        self.assertEqual(None, User.get_by_id(uid))


if __name__ == '__main__':
    unittest.main()
