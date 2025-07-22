# -*- coding: utf-8 -*-

import flask_admin as admin
import flask_login as login

from vulyk.admin.models import AuthModelView
from vulyk.models.user import User

__all__ = ["AuthAdminIndexView", "init_admin"]


class AuthAdminIndexView(admin.AdminIndexView):
    def is_accessible(self) -> bool:
        return login.current_user.is_authenticated and login.current_user.is_admin()


def init_admin(app) -> admin.Admin:
    adm = admin.Admin(app, "Vulyk: Admin", index_view=AuthAdminIndexView(), template_mode="bootstrap3")

    adm.add_view(AuthModelView(User))

    return adm
