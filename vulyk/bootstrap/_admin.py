# -*- coding: utf-8 -*-

import flask_login as login
import flask_admin as admin

from vulyk.models.user import User
from vulyk.admin.models import AuthModelView


__all__ = [
    'AuthAdminIndexView', 'init_admin'
]


class AuthAdminIndexView(admin.AdminIndexView):
    def is_accessible(self):
        return (
            login.current_user.is_authenticated and
            login.current_user.is_admin()
        )


def init_admin(app):
    adm = admin.Admin(
        app,
        'Vulyk: Admin',
        index_view=AuthAdminIndexView(),
        template_mode='bootstrap3'
    )

    adm.add_view(AuthModelView(User))

    return adm
