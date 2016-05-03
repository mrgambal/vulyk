# -*- coding: utf-8 -*-
"""Copy files from all static folders to root folder."""

import os

from flask_collect.storage.file import Storage as FileStorage
from werkzeug.utils import import_string

__all__ = ['Storage']


class PluginWrapper(object):
    """
    Creates Blueprint-like wrapper for our plugins
    """
    def __init__(self, plugin_name, root_url='/static', prefix=''):
        """
        Let's stub some dumb fields to get this one treated like a regular
        Flask blueprint while collecting static files.

        :param plugin_name: Plugin module name
        :type plugin_name: str
        :param root_url: Root static URL
        :type root_url: str
        """
        static_path = import_string(plugin_name).__path__[0]
        static_path = os.path.join(static_path, 'static')

        self.name = '{}{}'.format(prefix, plugin_name)
        self.static_url_path = '{}/{}/static'.format(root_url, self.name)
        self.static_folder = ''
        self.has_static_folder = os.path.isdir(static_path)

        if self.has_static_folder:
            self.static_folder = static_path


class Storage(FileStorage):
    """Storage that copies static files."""

    def __init__(self, collect, verbose=False):
        """
        Copy current array of blueprints and store it.
        Substitute the dict with the extended one which contains our plugins
        wrapped into a blueprint-like objects (PluginWrapper).

        Having that done allows standard FileStorage.run() iterate over
        static files inside of our plugins as well and collect them properly.
        """
        super(Storage, self).__init__(collect, verbose)

        blueprints = self.collect.app.blueprints
        self.old_blueprints = blueprints.copy()
        self.collect.app.blueprints = self._convert_plugins(blueprints)

    def _convert_plugins(self, blueprints):
        """
        Here we create stubs for our plugins with blueprint-like interface.

        :param blueprints: blueprints dict
        :type blueprints: dict

        :return: Blueprints and our wrappers for plugins
        :rtype: dict
        """
        enabled_tasks = self.collect.app.config.get('ENABLED_TASKS', {})
        prefix = self.collect.app.config.get('COLLECT_PLUGIN_DIR_PREFIX', '')
        static_url = self.collect.app.static_url_path

        for name, _ in enabled_tasks.items():
            plugin = PluginWrapper(name, static_url, prefix)
            blueprints[name] = plugin

        return blueprints

    def __del__(self):
        """
        Restore initial list of blueprints and remove the copy.
        """
        self.collect.app.blueprints = self.old_blueprints.copy()
        self.old_blueprints = None
