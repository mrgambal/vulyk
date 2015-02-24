# -*- coding=utf-8 -*-

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
        settings = {}
        task_settings = import_string(
            "{plugin_name}.settings".format(plugin_name=plugin)
        )
        for settings_key in dir(task_settings):
            settings[settings_key] = getattr(task_settings, settings_key)

        task_types[task] = settings

    return task_types
