from flask_admin.contrib.mongoengine import ModelView
import flask_login as login


class AuthModelView(ModelView):
    def is_accessible(self):
        return (
            login.current_user.is_authenticated and
            login.current_user.is_admin()
        )
