# -*- coding: utf-8 -*-
import os.path
from typing import List

from flask_assets import Bundle, Environment
from flask_collect import Collect

__all__ = [
    'init'
]


def _get_files_for_settings(app, assets_key) -> List[str]:
    """
    Extract a list of full paths to given assets group.

    :param app: Main application instance
    :type app: flask.Flask
    :param assets_key: Key which maps to a certain list of assets in settings.
    :type assets_key: str

    :returns: list of paths to assets
    :rtype: List[str]
    """
    result = []

    if assets_key in app.config and len(app.config[assets_key]) > 0:
        result = [
            os.path.join(app.static_folder, static_file)
            for static_file in app.config[assets_key]
        ]

    return result


def init(app) -> None:
    """
    Bundle projects assets.

    :param app: Main application instance
    :type app: flask.Flask
    """
    assets = Environment(app)
    assets.auto_build = app.config.get('ASSETS_AUTO_BUILD', True)
    files_to_watch = []

    if 'COLLECT_STATIC_ROOT' in app.config:
        assets.cache = app.config['COLLECT_STATIC_ROOT']
        collect = Collect()
        collect.init_app(app)
        collect.collect()
        app.static_folder = app.config['COLLECT_STATIC_ROOT']

    for key in ['js', 'css']:
        assets_key = '%s_ASSETS' % key.upper()
        build_files = app.config[assets_key]

        files_to_watch.extend(_get_files_for_settings(app, assets_key))

        bundle = Bundle(*build_files,
                        output=app.config['%s_OUTPUT' % assets_key],
                        filters=app.config['%s_FILTERS' % assets_key]
                        )

        assets.register('%s_all' % key, bundle)

        app.logger.debug('Bundling files: %s%s',
                         os.linesep,
                         os.linesep.join(build_files))

    app.assets = assets
    app._base_files_to_watch = files_to_watch

    app.logger.info('Base assets are collected successfully.')
