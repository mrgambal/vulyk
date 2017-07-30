# -*- coding: utf-8 -*-

from flask_admin.contrib.mongoengine import ModelView
import flask_login as login

__all__ = [
    'AuthModelView'
]


class AuthModelView(ModelView):
    def is_accessible(self):
        return (
            login.current_user.is_authenticated and
            login.current_user.is_admin()
        )
