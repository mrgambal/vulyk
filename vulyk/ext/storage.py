# -*- coding: utf-8 -*-
"""Copy files from all static folders to root folder."""

import os
from typing import Any

from flask_collect.storage.file import Storage as FileStorage
from werkzeug.utils import import_string

__all__ = ["Storage"]


class PluginWrapper:
    """
    Creates Blueprint-like wrapper for our plugins.
    """

    __slots__ = ["has_static_folder", "name", "static_folder", "static_url_path"]

    def __init__(self, plugin_name: str, root_url: str = "/static", prefix: str = "") -> None:
        """
        Let's stub some dumb fields to get this one treated like a regular
        Flask blueprint while collecting static files.

        :param plugin_name: Plugin module name.
        :param root_url: Root static URL.
        :param prefix: Prefix for plugin name.
        """
        static_path = import_string(plugin_name).__path__[0]
        static_path = os.path.join(static_path, "static")

        self.name = "{}{}".format(prefix, plugin_name)
        self.static_url_path = "{}/{}/static".format(root_url, self.name)
        self.static_folder = ""
        self.has_static_folder = os.path.isdir(static_path)

        if self.has_static_folder:
            self.static_folder = static_path


class Storage(FileStorage):
    """Storage that copies static files."""

    def __init__(self, collect, *, verbose: bool = False) -> None:
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

    def _convert_plugins(self, blueprints: dict[str, Any]) -> dict[str, PluginWrapper]:
        """
        Here we create stubs for our plugins with blueprint-like interface.

        :param blueprints: blueprints dict.
        :return: Blueprints and our wrappers for plugins.
        """
        enabled_tasks = self.collect.app.config.get("ENABLED_TASKS", {})
        prefix = self.collect.app.config.get("COLLECT_PLUGIN_DIR_PREFIX", "")
        static_url = self.collect.app.static_url_path

        for name, _ in enabled_tasks.items():
            plugin = PluginWrapper(name, static_url, prefix)
            blueprints[name] = plugin

        return blueprints

    def __del__(self) -> None:
        """
        Restore initial list of blueprints and remove the copy.
        """
        if self.old_blueprints is not None:
            self.collect.app.blueprints = self.old_blueprints.copy()
            self.old_blueprints = None
