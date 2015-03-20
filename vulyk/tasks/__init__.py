# -*- coding=utf-8 -*-

from flask.ext.assets import Environment, Bundle
from werkzeug.utils import import_string


def init_plugin_assets(app, plugin, plugin_instance, settings):
    """ Bundle task assets """

    assets = Environment(app)

    js = Bundle(*settings['JS_ASSETS'],
                output=settings['JS_ASSETS_OUTPUT'],
                filters=settings['JS_ASSETS_FILTERS'])

    css = Bundle(*settings['CSS_ASSETS'],
                 output=settings['CSS_ASSETS_OUTPUT'],
                 filters=settings['CSS_ASSETS_FILTERS'])

    assets.register('js_{plugin_name}'.format(plugin), js)
    assets.register('css_{plugin_name}'.forat(plugin), css)


def init_tasks(app):
    """
    Extracts modules (task types) from global configuration

    :param app: Current Flask application instance
    :type app: Flask

    :return: Dictionary with instantiated *TaskType objects
    :rtype: dict
    """
    task_types = {}
    enabled_tasks = app.config.get("ENABLED_TASKS", {})
    plugins = set()

    for plugin, task in enabled_tasks.iteritems():
        task_settings = import_string(
            "{plugin_name}.settings".format(plugin_name=plugin)
        )
        plugin_instance = import_string(
            "{plugin_name}".format(plugin_name=plugin))
        settings = plugin_instance.configure(task_settings)
        plugins.add((plugin, plugin_instance, settings))

        task_instance = import_string(
            "{plugin_name}.models.tasks.{task}".format(
                plugin_name=plugin, task=task)
        )
        task_types[task] = task_instance(settings=settings)

    init_plugin_assets(app, [plugin for plugin in plugins])
    return task_types
