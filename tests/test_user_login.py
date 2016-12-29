# -*- coding: utf-8 -*-
"""
test_user_login
"""
import flask
import mongomock
from mongoengine import Document
from unittest.mock import patch

from vulyk import users
from vulyk.models.user import User

from .base import (
    BaseTest,
    DBTestHelpers)


class TestUserLogin(BaseTest):
    USER = User(username='SuperUsername', email='1@email.com', admin=True)

    def tearDown(self):
        DBTestHelpers.collections.user.drop()
        DBTestHelpers.collections.groups.drop()

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    @patch('flask_login.current_user', USER)
    def test_injected_in_request(self):
        app = flask.Flask("test")
        app.config.from_object('vulyk.settings')
        db = mongomock.MongoClient().get_database('vulyk')
        db.Document = Document

        users.init_social_login(app, db)

        def fake_route():
            self.assertEqual(flask.g.user, self.USER)
            return flask.Response()

        app.route('/test', methods=['GET'])(fake_route)
        app.test_client().get('/test')

    @patch('mongoengine.connection.get_connection', DBTestHelpers.connection)
    @patch('flask_login.current_user', USER)
    def test_injected_in_template(self):
        app = flask.Flask('test')
        app.config.from_object('vulyk.settings')
        db = mongomock.MongoClient().get_database('vulyk')
        db.Document = Document

        users.init_social_login(app, db)

        def fake_route():
            return flask.render_template_string("{{user}}")

        app.route('/test', methods=['GET'])(fake_route)
        resp = app.test_client().get('/test')

        self.assertEqual(resp.data.decode('utf8'), self.USER.username)
