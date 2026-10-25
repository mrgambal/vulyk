=====
Usage
=====

Running the application
-----------------------

The main entry points are:

- ``manage.py`` – convenience wrapper for the Click CLI;
- ``vulyk.control:cli`` – the underlying management commands;
- ``vulyk.app:app`` – the bootstrapped Flask application.

The simplest local run command is:

.. code-block:: bash

    uv run manage.py run

You can also expose the Flask app directly from Python if another process is
embedding Vulyk:

.. code-block:: python

    from vulyk.app import app

Social-auth routes are registered during bootstrap. To test the full browser
login flow locally, configure at least one provider supported by
``vulyk.settings``.

Task configuration
------------------

Task plugins are enabled through ``ENABLED_TASKS`` in ``local_settings.py``.
Each mapping entry has the form ``{"package_name": "TaskTypeClassName"}``.

Example:

.. code-block:: python

    ENABLED_TASKS = {
        "vulyk_declaration": "DeclarationTaskType",
        "vulyk_tagging": "TaggingTaskType",
    }

Optional blueprints are configured through ``ENABLED_BLUEPRINTS``. The built-in
gamification blueprint is enabled by default in ``vulyk.settings``.

Data loading
------------

Before users can work on tasks, initialize the default group with the task
types you want to expose:

.. code-block:: bash

    uv run manage.py init declaration_task tagging_task

Load tasks from JSON Lines data. Plain text, ``.gz``, and ``.bz2`` inputs are
supported.

.. code-block:: bash

    uv run manage.py db load declaration_task --batch 01_declaration decl_tasks.jsonl
    uv run manage.py db load tagging_task --batch 01_tagging tagging_tasks.jsonl

When a batch is created, Vulyk stores batch-level metadata and tracks progress
through ``tasks_count`` and ``tasks_processed``.

Task lifecycle
--------------

For each enabled task type, the core workflow is:

1. ``get_next()`` finds an open task the current user has not processed yet,
   preferring open batches and avoiding skipped tasks until nothing else is
   available.
2. Starting a task opens or refreshes a ``WorkSession``.
3. ``on_task_done()`` stores an answer, updates the task and user counters,
   closes the work session, and advances the parent batch if the task closed.
4. ``skip_task()`` records the skip and removes the active work session.

Operational commands
--------------------

Useful CLI commands include:

.. code-block:: bash

    uv run manage.py group list
    uv run manage.py group add
    uv run manage.py batches list
    uv run manage.py stats batch
    uv run manage.py db export declaration_task reports.jsonl --with-sessions

``db export --with-sessions`` enriches exported answers with work-session start,
end, duration, and activity fields when matching sessions exist.

Admin and blueprints
--------------------

Set ``ENABLE_ADMIN = True`` to register the admin UI. When enabled, the built-in
gamification module can also contribute admin views and routes under the
configured ``url_prefix``.

If static assets are collected into a shared directory, Vulyk can resolve
plugin files from ``COLLECT_STATIC_ROOT`` using the
``COLLECT_PLUGIN_DIR_PREFIX`` naming convention.
