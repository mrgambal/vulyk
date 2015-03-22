# -*- coding=utf-8 -*-
import os.path
import jinja2
from werkzeug.utils import import_string

from flask.ext.assets import Bundle


def init_tasks(app):
    """
    Extracts modules (task types) from global configuration

    :param app: Current Flask application instance
    :type app: Flask

    :return: Dictionary with instantiated *TaskType objects
    :rtype: dict
    """
    task_types = {}
    loaders = {}
    enabled_tasks = app.config.get("ENABLED_TASKS", {})

    for plugin, task in enabled_tasks.iteritems():
        task_settings = import_string(
            "{plugin_name}.settings".format(plugin_name=plugin)
        )
        plugin_instance = import_string(
            "{plugin_name}".format(plugin_name=plugin))
        settings = plugin_instance.configure(task_settings)

        task_instance = import_string(
            "{plugin_name}.models.tasks.{task}".format(
                plugin_name=plugin, task=task)
        )
        static_path = import_string(plugin).__path__[0]

        js_name = 'plugin_js_{task}'.format(task=task_instance.type_name)
        css_name = 'plugin_css_{task}'.format(task=task_instance.type_name)

        # Problem below is that if JS_ASSETS/CSS_ASSETS are empty
        # webassets will throw an exception
        js = Bundle(*map(lambda x: os.path.join(static_path, x),
                         task_instance.JS_ASSETS),
                    output="scripts/{name}.js".format(name=js_name),
                    filters=app.config.get('JS_ASSETS_FILTERS', ''))

        css = Bundle(*map(lambda x: os.path.join(static_path, x),
                          task_instance.CSS_ASSETS),
                     output="styles/{name}.css".format(name=css_name),
                     filters=app.config.get('CSS_ASSETS_FILTERS', ''))

        app.assets.register(js_name, js)
        app.assets.register(css_name, css)
        loaders[task_instance.type_name] = jinja2.PackageLoader(plugin)

        task_types[task_instance.type_name] = task_instance(settings=settings)

    app.jinja_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.PrefixLoader(loaders)])

    return task_types
