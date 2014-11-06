# coding=utf-8
from flask.ext.assets import Environment, Bundle


def init(app):
    assets = Environment(app)
    js = Bundle(*app.config['JS_ASSETS'],
                output=app.config['JS_ASSETS_OUTPUT'],
                filters=app.config['JS_ASSETS_FILTERS'])

    css = Bundle(*app.config['CSS_ASSETS'],
                 output=app.config['CSS_ASSETS_OUTPUT'],
                 filters=app.config['CSS_ASSETS_FILTERS'])

    assets.register('js_all', js)
    assets.register('css_all', css)
