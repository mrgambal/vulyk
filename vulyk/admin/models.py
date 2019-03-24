# -*- coding: utf-8 -*-

import flask_login as login
import wtforms
from flask_admin.contrib.mongoengine import ModelView

__all__ = [
    'AuthModelView'
]


class CKTextAreaWidget(wtforms.widgets.TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(wtforms.fields.TextAreaField):
    widget = CKTextAreaWidget()


class RequiredBooleanField(wtforms.fields.SelectField):
    # Fucking wtforms/flask-admin has a flaw related
    # to boolean fields with required=True in the model
    # Ultimatelly false values wouldn't pass validation of the form
    # thus the workaround
    def __init__(self, *args, **kwargs) -> None:
        choices = [
            (True, 'True'),
            (False, 'False'),
        ]

        kwargs['choices'] = choices
        kwargs['coerce'] = lambda x: str(x) == 'True'

        super(RequiredBooleanField, self).__init__(*args, **kwargs)


class AuthModelView(ModelView):
    """
    Model view that requires authentication and admin status
    Comes with useful extra of wysiwyg field
    """
    extra_js = ['//cdn.ckeditor.com/4.7.1/standard/ckeditor.js']

    def is_accessible(self) -> bool:
        return (
            login.current_user.is_authenticated and
            login.current_user.is_admin()
        )
