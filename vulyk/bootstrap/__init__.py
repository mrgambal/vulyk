# -*- coding: utf-8 -*-
"""
Project bootstrapper.

Contains code not to be used directly after the initialization.
"""
import flask
from flask_mongoengine import MongoEngine

from . import _assets, _blueprints, _logging, _social_login
from ._tasks import init_plugins

__all__ = [
    'init_app',
    'init_plugins'
]


# region Init
def init_app(name):
    """
    :param name: application alias
    :type name: str

    :return: Bootstrapped cached application instance
    :rtype: flask.Flask
    """
    key = 'app'

    if not hasattr(init_app, key):
        app = flask.Flask(name)

        app.config.from_object('vulyk.settings')

        try:
            app.config.from_object('local_settings')
        except ImportError:
            pass

        app.template_folder = app.config.get('TEMPLATES_FOLDER', 'templates')
        app.static_folder = app.config.get('STATIC_FOLDER', 'static')

        _logging.init_logger(app=app)
        app.logger.info('STARTING.')

        db = MongoEngine(app)

        app.logger.debug('Database is available at %s:%s',
                         app.config['MONGODB_SETTINGS'].get('HOST',
                                                            'localhost'),
                         app.config['MONGODB_SETTINGS'].get('PORT', 27017))

        _assets.init(app)
        _social_login.init_social_login(app, db)

        if app.config.get('ENABLE_ADMIN', False):
            from . import _admin
            app.admin = _admin.init_admin(app)

        _blueprints.init_blueprints(app)

        setattr(init_app, key, app)

        app.logger.info('Vulyk bootstrapping complete.')

    return getattr(init_app, key)
# endregion Init
