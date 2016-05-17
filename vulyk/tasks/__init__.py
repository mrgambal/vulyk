# -*- coding=utf-8 -*-
import os.path

import jinja2
from flask_assets import Bundle
from werkzeug.utils import import_string


def init_tasks(app):
    """
    Extracts modules (task types) from global configuration

    :param app: Current Flask application instance
    :type app: flask.Flask

    :return: Dictionary with instantiated *TaskType objects
    :rtype: dict
    """
    task_types = {}
    loaders = {}
    enabled_tasks = app.config.get('ENABLED_TASKS', {})
    files_to_watch = []

    for plugin, task in enabled_tasks.items():
        task_settings = import_string(
            '{plugin_name}.settings'.format(plugin_name=plugin)
        )
        plugin_instance = import_string(
            '{plugin_name}'.format(plugin_name=plugin))
        settings = plugin_instance.configure(task_settings)

        task_instance = import_string(
            '{plugin_name}.models.task_types.{task}'.format(
                plugin_name=plugin, task=task)
        )

        loaders[task_instance.type_name] = jinja2.PackageLoader(plugin)
        task_types[task_instance.type_name] = task_instance(settings=settings)

        default_static_path = plugin_instance.__path__[0]
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

        js_name = 'plugin_js_{task}'.format(task=task_instance.type_name)
        css_name = 'plugin_css_{task}'.format(task=task_instance.type_name)

        if len(task_instance.JS_ASSETS) > 0:
            files_to_watch += map(
                lambda x: os.path.join(default_static_path, x),
                task_instance.JS_ASSETS)

            js = Bundle(*map(lambda x: os.path.join(static_path, x),
                             task_instance.JS_ASSETS),
                        output='scripts/{name}.js'.format(name=js_name),
                        filters=app.config.get('JS_ASSETS_FILTERS', ''))
            app.assets.register(js_name, js)

        if len(task_instance.CSS_ASSETS) > 0:
            files_to_watch += map(
                lambda x: os.path.join(default_static_path, x),
                task_instance.CSS_ASSETS)

            css = Bundle(*map(lambda x: os.path.join(static_path, x),
                              task_instance.CSS_ASSETS),
                         output='styles/{name}.css'.format(name=css_name),
                         filters=app.config.get('CSS_ASSETS_FILTERS', ''))

            app.assets.register(css_name, css)

    app.jinja_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.PrefixLoader(loaders)])

    app._plugin_files_to_watch = files_to_watch

    return task_types
