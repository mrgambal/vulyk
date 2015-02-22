# -*- coding: utf-8 -*-
from os import listdir
from os.path import isfile, join

from flask.ext.assets import Environment, Bundle


def init(app):
    assets = Environment(app)

    enabled_tasks = app.config.get("ENABLED_TASKS", {})
    for plugin in enabled_tasks:
        plugin = plugin.replace('.', '/')
        js_path = '{plugin_name}/static/scripts'.format(plugin_name=plugin)
        css_path = '{plugin_name}/static/styles'.format(plugin_name=plugin)

        jsfiles = [f for f in listdir(js_path) if isfile(join(js_path, f))]
        cssfiles = [f for f in listdir(css_path) if isfile(join(css_path, f))]

        for jsfile in jsfiles:
            app.config['JS_ASSETS'].append(jsfile)

        for cssfile in cssfiles:
            app.config['CSS_ASSETS'].append(cssfile)

    js = Bundle(*app.config['JS_ASSETS'],
                output=app.config['JS_ASSETS_OUTPUT'],
                filters=app.config['JS_ASSETS_FILTERS'])

    css = Bundle(*app.config['CSS_ASSETS'],
                 output=app.config['CSS_ASSETS_OUTPUT'],
                 filters=app.config['CSS_ASSETS_FILTERS'])

    assets.register('js_all', js)
    assets.register('css_all', css)
