============
Installation
============

Quick Start
-----------

Prerequisites:

- Python 3.10+
- `uv` (https://github.com/astral-sh/uv)
- MongoDB running on localhost:27017 (or a custom connection configured in
  ``local_settings.py`` / environment variables)
- At least one Vulyk-compatible task plugin installed into the same
  environment

To install Vulyk from source:

.. code-block:: bash

    git clone https://github.com/mrgambal/vulyk.git
    cd vulyk
    uv sync --dev

Install one or more task plugins in editable mode if you want to run the web
application with real task types:

.. code-block:: bash

    uv pip install -e ../vulyk-declaration
    uv pip install -e ../vulyk-tagging

Create ``local_settings.py`` in the repository root. The application imports it
after ``vulyk.settings``, so it is the recommended place for local overrides.

Minimal example:

.. code-block:: python

    MONGODB_SETTINGS = {
        "DB": "vulyk",
        "HOST": "localhost",
        "PORT": 27017,
    }

    ENABLED_TASKS = {
        "vulyk_declaration": "DeclarationTaskType",
        "vulyk_tagging": "TaggingTaskType",
    }

    ENABLED_BLUEPRINTS = [
        {
            "path": "vulyk.blueprints.gamification.gamification",
            "config": {},
            "url_prefix": "gamification",
        }
    ]

The base settings also read environment variables for values such as
``SECRET_KEY``, MongoDB connection fields, logging options, and social-auth
credentials. Dependency and tool definitions are maintained in
``pyproject.toml``.

To initialize the default permission group and start the service:

.. code-block:: bash

    uv run manage.py init declaration_task tagging_task
    uv run manage.py run

To verify installation:

.. code-block:: bash

    uv run -m unittest

Tests use the ``vulyk_test`` database on the same MongoDB server.
