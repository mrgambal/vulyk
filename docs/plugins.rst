=============================
Writing plugins for Vulyk
=============================

Vulyk task types are implemented as regular Python packages installed into the
same environment as the core application.

At startup, ``vulyk.bootstrap.init_plugins()`` reads ``ENABLED_TASKS`` and, for
each configured plugin package:

1. imports ``<plugin>.settings``;
2. imports the top-level plugin package and calls ``configure(settings)``;
3. imports ``<plugin>.models.task_types.<TaskTypeClass>``;
4. instantiates that task type class;
5. registers plugin templates and static assets.

Plugin package shape
--------------------

A typical plugin package looks like this:

.. code-block:: text

    name_of_plugin/
        __init__.py
        settings.py
        models/
            __init__.py
            task_types.py
            tasks.py
        static/
            images/
            scripts/
            styles/
        templates/
            *.html

Runtime contract
----------------

Each task type class should inherit from
``vulyk.models.task_types.AbstractTaskType`` and define at least:

- ``task_model`` – a subclass of ``AbstractTask``;
- ``answer_model`` – a subclass of ``AbstractAnswer``;
- ``type_name`` – the internal task type identifier;
- ``template`` – the task UI template.

Useful optional attributes and hooks include:

- ``redundancy`` – answers required before a task closes;
- ``JS_ASSETS`` / ``CSS_ASSETS`` – plugin asset bundles;
- ``_task_type_meta`` – default metadata copied into created batches;
- ``_is_ready_for_autoclose(...)`` – custom early-closing logic.

What the core framework gives you
---------------------------------

By inheriting from ``AbstractTaskType`` you automatically get:

- task import from JSON Lines files;
- task selection that prefers open batches and avoids already processed tasks;
- skip handling;
- answer persistence;
- leaderboard aggregation;
- work-session tracking;
- report export, including optional session timing metadata.

Configuration
-------------

Enable a plugin in ``local_settings.py`` by mapping the package import name to
the task type class name:

.. code-block:: python

    ENABLED_TASKS = {
        "vulyk_declaration": "DeclarationTaskType",
        "vulyk_tagging": "TaggingTaskType",
    }

The package name must be importable in the current environment, and the task
type class must be available from ``<plugin>.models.task_types``.

Templates and static assets
---------------------------

Vulyk registers a ``jinja2.PackageLoader`` for each enabled plugin, so plugin
templates can live inside the package. Static assets referenced through
``JS_ASSETS`` and ``CSS_ASSETS`` are bundled with Flask-Assets.

If the deployment uses ``COLLECT_STATIC_ROOT``, plugin assets are resolved from
the collected static directory using ``COLLECT_PLUGIN_DIR_PREFIX``; otherwise
they are loaded directly from the plugin package path.

Data format expectations
------------------------

``manage.py db load`` expects JSON Lines input: one valid JSON object per line.
Compressed ``.gz`` and ``.bz2`` sources are supported.

For broader runtime and CLI details, see ``README.rst`` and ``docs/usage.rst``.
