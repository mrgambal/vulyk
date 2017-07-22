# -*- coding: utf-8 -*-
"""
Project bootstrapper.

Contains code not to be used directly after the initialization.
"""
import flask
from werkzeug.utils import import_string
from flask_mongoengine import MongoEngine

from . import _assets, _logging, _social_login
from ._tasks import init_plugins
from vulyk.blueprints import VulykModule

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

        _logging.init_logger(app=app)
        app.logger.info('STARTING.')

        db = MongoEngine(app)

        app.logger.debug('Database is available at %s:%s',
                         app.config['MONGODB_SETTINGS'].get('HOST',
                                                            'localhost'),
                         app.config['MONGODB_SETTINGS'].get('PORT', 27017))

        _assets.init(app)
        _social_login.init_social_login(app, db)

        enabled_blueprints = app.config.get('ENABLED_BLUEPRINTS', [])
        for blueprint in enabled_blueprints:
            try:
                blueprint_obj = import_string(blueprint['path'])
                if not isinstance(blueprint_obj, VulykModule):
                    raise ImportError

                blueprint_obj.configure(blueprint.get('config', {}))

                app.register_blueprint(
                    blueprint_obj, url_prefix="/{}".format(blueprint["url_prefix"])
                )

                app.logger.info('Blueprint {} loaded successfully.'.format(
                    blueprint.get("path"))
                )
            except (ImportError, KeyError) as e:
                app.logger.warning('Cannot load blueprint {}: {}.'.format(
                    blueprint.get("path"), e)
                )

        setattr(init_app, key, app)

        app.logger.info('Vulyk bootstrapping complete.')

    return getattr(init_app, key)
# endregion Init
