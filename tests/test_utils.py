# -*- coding: utf-8 -*-
"""
test_utils
"""
from unittest.mock import patch, Mock
from werkzeug.exceptions import HTTPException

from vulyk import utils
from vulyk.models.user import User, Group

from .base import (
    BaseTest,
    DBTestHelpers
)
from .fixtures import FakeType


class TestUtils(BaseTest):
    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def setUp(self):
        super().setUp()

        Group.objects.create(
            id='default',
            description='test',
            allowed_types=[FakeType.type_name])

    def test_unique(self):
        self.assertEqual([2, 4, 6, 8], utils.unique([2, 2, 4, 2, 6, 4, 8]),
                         'Unique function returns duplicates')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_resolve_task_type_ok(self):
        task_type = FakeType({})
        tasks = {task_type.type_name: task_type}
        user = User(username='1', email='1@email.com').save()

        self.assertEqual(
            utils.resolve_task_type(task_type.type_name, tasks, user),
            task_type,
            'Task type should have been resolved, but hasn\'t'
        )

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    def test_resolve_task_type_not_found(self):
        tasks = {}
        user = User(username='1', email='1@email.com').save()

        with self.assertRaises(HTTPException) as he:
            utils.resolve_task_type('BS_group', tasks, user)

        self.assertEqual(he.exception.code, utils.HTTPStatus.NOT_FOUND,
                         'Http 404 exception didn\'t fire')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
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

    def tearDown(self):
        DBTestHelpers.collections.user.drop()
        DBTestHelpers.collections.groups.drop()
