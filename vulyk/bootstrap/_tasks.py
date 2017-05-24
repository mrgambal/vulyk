# -*- coding: utf-8 -*-
"""Module contains code that performs plugins initialisation."""

import os.path

import jinja2
from flask_assets import Bundle
from werkzeug.utils import import_string


__all__ = [
    'init_plugins'
]


def _init_plugin_assets(app, task_type, static_path):
    """
    Bundle plugin static files.

    :param app: Main application instance.
    :type app: flask.Flask
    :param task_type: Plugin root instance.
    :type task_type: vulyk.models.task_types.AbstractTaskType
    :param static_path: Path to plugin's static folder.
    :type static_path: str

    :return: List of paths to plugin's asset files.
    :rtype: list[str]
    """
    files_to_watch = []
    assets_location_map = {
        'js': task_type.JS_ASSETS,
        'css': task_type.CSS_ASSETS
    }

    for key in assets_location_map.keys():
        name = 'plugin_{key}_{task}'.format(key=key, task=task_type.type_name)
        assets_list = assets_location_map[key]

        if len(assets_list) > 0:
            files_to_watch += map(lambda x: os.path.join(static_path, x),
                                  assets_list)

            folder = ['scripts', 'styles'][key == 'css']
            filters_name = '{key}_ASSETS_FILTERS'.format(key=key.upper())
            output_path = '{folder}/{name}.{key}'.format(folder=folder,
                                                         name=name,
                                                         key=key)
            bundle = Bundle(*map(lambda x: os.path.join(static_path, x),
                                 assets_list),
                            output=output_path,
                            filters=app.config.get(filters_name, ''))
            app.assets.register(name, bundle)

    return files_to_watch


def init_plugins(app):
    """
    Extracts modules (task types) from global configuration.

    :param app: Current Flask application instance
    :type app: flask.Flask

    :return: Dictionary with instantiated TaskType objects
    :rtype: dict[str, vulyk.models.task_types.AbstractTaskType]
    """
    task_types = {}
    loaders = {}
    enabled_tasks = app.config.get('ENABLED_TASKS', {})
    files_to_watch = []

    for plugin, task in enabled_tasks.items():
        task_settings = import_string(
            '{plugin_name}.settings'.format(plugin_name=plugin)
        )
        plugin_type = import_string(
            '{plugin_name}'.format(plugin_name=plugin))
        settings = plugin_type.configure(task_settings)

        task_type = import_string(
            '{plugin_name}.models.task_types.{task}'.format(
                plugin_name=plugin, task=task)
        )

        loaders[task_type.type_name] = jinja2.PackageLoader(plugin)
        task_types[task_type.type_name] = task_type(settings=settings)

        default_static_path = plugin_type.__path__[0]
        # if Flask-Collect is enabled - get files from collected dir
        if 'COLLECT_STATIC_ROOT' in app.config:
            # all plugin static goes stored in a dir may have prefixed name
            # to prevent any collision e.g. plugin named 'images'
            prefix = app.config.get('COLLECT_PLUGIN_DIR_PREFIX', '')
            static_path = os.path.join(app.static_folder,
                                       '{}{}'.format(prefix, plugin))
        # else - use standard static folder
        else:
            static_path = default_static_path

        files_to_watch.extend(_init_plugin_assets(
            app=app,
            task_type=task_type,
            static_path=static_path))

    app.jinja_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.PrefixLoader(loaders)])

    app._plugin_files_to_watch = files_to_watch

    return task_types
