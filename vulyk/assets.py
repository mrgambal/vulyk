# -*- coding: utf-8 -*-
from flask.ext.assets import Environment, Bundle
from flask.ext.collect import Collect


def init(app):
    """
    Bundle projects assets

    :type app: flask.Flask
    """
    assets = Environment(app)
    assets.auto_build = app.config.get('ASSETS_AUTO_BUILD', True)

    if 'COLLECT_STATIC_ROOT' in app.config:
        collect = Collect()
        collect.init_app(app)
        collect.collect()
        app.static_folder = app.config['COLLECT_STATIC_ROOT']\

    if 'JS_ASSETS' in app.config and len(app.config['JS_ASSETS']) > 0:
        js = Bundle(*app.config['JS_ASSETS'],
                    output=app.config['JS_ASSETS_OUTPUT'],
                    filters=app.config['JS_ASSETS_FILTERS'])
        assets.register('js_all', js)

    if 'CSS_ASSETS' in app.config and len(app.config['CSS_ASSETS']) > 0:
        css = Bundle(*app.config['CSS_ASSETS'],
                     output=app.config['CSS_ASSETS_OUTPUT'],
                     filters=app.config['CSS_ASSETS_FILTERS'])
        assets.register('css_all', css)

    app.assets = assets
