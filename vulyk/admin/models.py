# -*- coding: utf-8 -*-

from flask_admin.contrib.mongoengine import ModelView
import flask_login as login
import wtforms

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


class AuthModelView(ModelView):
    """
    Model view that requires authentication and admin status
    Comes with useful extra of wysiwyg field
    """
    extra_js = ['//cdn.ckeditor.com/4.7.1/standard/ckeditor.js']

    def is_accessible(self):
        return (
            login.current_user.is_authenticated and
            login.current_user.is_admin()
        )
