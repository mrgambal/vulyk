# -*- coding: utf-8 -*-
"""Module contains stuff related to interoperability with PSA."""

import datetime

from flask import g
import flask_login as login
from social_flask_mongoengine.models import init_social
from social_flask.routes import social_auth
from social_flask.template_filters import backends

from vulyk.models.user import User

__all__ = [
    'init_social_login'
]


def init_social_login(app, db):
    """
    Login manager initialisation.

    :param app: Main application instance
    :type app: flask.Flask
    :param db: MongoDB wrapper instance
    :type db: flask_mongoengine.MongoEngine
    """
    app.register_blueprint(social_auth)
    init_social(app, db)

    login_manager = login.LoginManager()
    login_manager.login_view = 'index'
    login_manager.login_message = ''
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(userid):
        try:
            user = User.objects.get(id=userid)
            if user:
                user.last_login = datetime.datetime.now()
                user.save()
            return user
        except (TypeError, ValueError, User.DoesNotExist):
            return None

    @app.before_request
    def global_user():
        g.user = login.current_user

    @app.context_processor
    def inject_user():
        try:
            return {'user': g.user}
        except AttributeError:
            return {'user': None}

    app.context_processor(backends)
    app.logger.info('Social login subsystem is initialized.')
