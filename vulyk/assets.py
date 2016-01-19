# -*- coding: utf-8 -*-
import os.path
from flask.ext.assets import Environment, Bundle
from flask.ext.collect import Collect


def init(app):
    """
    Bundle projects assets

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

    if 'JS_ASSETS' in app.config and len(app.config['JS_ASSETS']) > 0:
        files_to_watch += [
            os.path.join(app.static_folder, js_file)
            for js_file in app.config['JS_ASSETS']
        ]

        js = Bundle(*app.config['JS_ASSETS'],
                    output=app.config['JS_ASSETS_OUTPUT'],
                    filters=app.config['JS_ASSETS_FILTERS'])
        assets.register('js_all', js)

    if 'CSS_ASSETS' in app.config and len(app.config['CSS_ASSETS']) > 0:
        files_to_watch += [
            os.path.join(app.static_folder, css_file)
            for css_file in app.config['CSS_ASSETS']
        ]

        css = Bundle(*app.config['CSS_ASSETS'],
                     output=app.config['CSS_ASSETS_OUTPUT'],
                     filters=app.config['CSS_ASSETS_FILTERS'])
        assets.register('css_all', css)

    app.assets = assets
    app._base_files_to_watch = files_to_watch
