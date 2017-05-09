=============================
Writing your plugin for Vulyk
=============================

Vulyk plugins are the python package, installable in the same environment where Vulyk is installed.

Your plugin for Vulyk should follow the standard structure and rules of writing Python package.

To create new plugin you can use http://cookiecutter.readthedocs.org/en/latest/ [[!insert link]] app with special template [[!link to plugin template]], by

.. >cookiecutter https://github.com/[[!link to plugin template]]


----------------
Plugin structure
----------------


- name_of_plugin
    - __init__.py
    - settings.py
    - models
        - __init__.py
        - task_types.py
        - tasks.py

    - static
        - images
        - scripts
        - styles
    - templates
        - \*.html

Main entrance point to plugin will be ``AbstractTaskType.get_task()``

-------------
Configuration
-------------

After plugin is installed in Vulyk environment, you need to enable it in Vulyk settings, by adding plugin's name to ENABLED_PLUGINS and name of the task to ENABLED_TASKS.

After Vulyk restart, plugin will be enabled.
