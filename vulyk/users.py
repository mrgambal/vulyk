# coding=utf-8
from flask import g
from flask.ext import login
from social.apps.flask_app.routes import social_auth
from social.apps.flask_app.me.models import init_social
from social.apps.flask_app.template_filters import backends
from models import User
import datetime


def init_social_login(app, db):
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
