# -*- coding=utf-8 -*-

from flask.ext.assets import Bundle
from werkzeug.utils import import_string


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

        js_name = 'js_{plugin}_{task}'.format(plugin=plugin, task=task)
        css_name = 'css_{plugin}_{task}'.format(plugin=plugin, task=task)

        js = Bundle(*task_instance.JS_ASSETS,
                    output="scripts/{name}.js".format(name=js_name),
                    filters=app.config.get('JS_ASSETS_FILTERS', ''))

        css = Bundle(*task_instance.CSS_ASSETS,
                     output="styles/{name}.css".format(name=css_name),
                     filters=app.config.get('CSS_ASSETS_FILTERS', ''))

        app.assets.register(js_name, js)
        app.assets.register(css_name, css)
        settings['js'] = js
        settings['css'] = css
        task_types[task] = task_instance(settings=settings)

    return task_types
