# -*- coding: utf-8 -*-
"""
test_user_login
"""
import flask
from mongoengine import connect, Document
from unittest.mock import patch

from vulyk.bootstrap import _social_login as social_login
from vulyk.models.user import Group, User

from .base import BaseTest


class TestUserLogin(BaseTest):
    USER = User(username='SuperUsername', email='1@email.com', admin=True)

    def tearDown(self):
        User.objects.delete()
        Group.objects.delete()

        super().tearDown()

    @patch('flask_login.current_user', USER)
    def test_injected_in_request(self):
        app = flask.Flask('test')
        app.config.from_object('vulyk.settings')
        db = connect(host='mongodb://localhost:27017').vulyk_test
        db.Document = Document

        social_login.init_social_login(app, db)

        def fake_route():
            self.assertEqual(flask.g.user, self.USER)
            return flask.Response()

        app.route('/test', methods=['GET'])(fake_route)
        app.test_client().get('/test')

    @patch('flask_login.current_user', USER)
    def test_injected_in_template(self):
        app = flask.Flask('test')
        app.config.from_object('vulyk.settings')
        db = connect(host='mongodb://localhost:27017').vulyk_test
        db.Document = Document

        social_login.init_social_login(app, db)

        def fake_route():
            return flask.render_template_string('{{user}}')

        app.route('/test', methods=['GET'])(fake_route)
        resp = app.test_client().get('/test')

        self.assertEqual(resp.data.decode('utf8'), self.USER.username)
