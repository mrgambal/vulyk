# -*- coding: utf-8 -*-
"""
test_utils
"""
import unittest
from unittest.mock import Mock

from werkzeug.exceptions import HTTPException

from vulyk import utils
from vulyk.models.user import Group, User

from .base import BaseTest
from .fixtures import FakeType


class TestUtils(BaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            id='default',
            description='test',
            allowed_types=[FakeType.type_name])

    @classmethod
    def tearDownClass(cls):
        Group.objects.delete()

        super().tearDownClass()

    def tearDown(self):
        User.objects.delete()

        super().tearDown()

    def test_resolve_task_type_ok(self):
        task_type = FakeType({})
        tasks = {task_type.type_name: task_type}
        user = User(username='1', email='1@email.com').save()

        self.assertEqual(
            utils.resolve_task_type(task_type.type_name, tasks, user),
            task_type,
            'Task type should have been resolved, but hasn\'t'
        )

    def test_resolve_task_type_not_found(self):
        tasks = {}
        user = User(username='1', email='1@email.com').save()

        with self.assertRaises(HTTPException) as he:
            utils.resolve_task_type('BS_group', tasks, user)

        self.assertEqual(he.exception.code, utils.HTTPStatus.NOT_FOUND,
                         'Http 404 exception didn\'t fire')

    def test_resolve_task_type_forbidden(self):
        task_type = FakeType({})
        user = User(username='1', email='1@email.com').save()
        tasks = {'secret_type': task_type}

        with self.assertRaises(HTTPException) as he:
            utils.resolve_task_type('secret_type', tasks, user)

        self.assertEqual(he.exception.code, utils.HTTPStatus.FORBIDDEN,
                         'Http 403 exception didn\'t fire')

    def test_chunked(self):
        self.assertEqual(
            [x for x in utils.chunked([1, 2, 3, 4, 5], 2)],
            [(1, 2), (3, 4), (5,)],
            'Wrong chunks were made.'
        )

    def test_get_template_path_in_templates(self):
        app = Mock()
        app.jinja_loader = Mock()
        app.jinja_loader.list_templates = lambda: [
            'templates/shekels/base/shekel.html'
        ]
        app.config = {'TEMPLATE_BASE_FOLDERS': [
            'templates/shekels',
        ]}

        self.assertEqual(
            utils.get_template_path(app, 'shekel.html'),
            'templates/shekels/base/shekel.html'
        )

    def test_get_template_path_in_stubs(self):
        app = Mock()
        app.jinja_loader = Mock()
        app.jinja_loader.list_templates = lambda: []
        app.config = {'TEMPLATE_BASE_FOLDERS': ['/']}

        self.assertEqual(
            utils.get_template_path(app, 'shekel.html'),
            'base/shekel.html'
        )


if __name__ == '__main__':
    unittest.main()
