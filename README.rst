Crowdsourcing platform for various tasks
========================================

.. image:: https://github.com/mrgambal/vulyk/workflows/MatrixTest/badge.svg
        :target: https://github.com/mrgambal/vulyk/actions

.. image:: https://readthedocs.org/projects/vulyk/badge/?version=latest
        :target: https://vulyk.readthedocs.org/en/latest/

.. image:: https://codecov.io/github/mrgambal/vulyk/graph/badge.svg?token=hLG1y2FiEa 
        :target: https://codecov.io/github/mrgambal/vulyk

License
-------

- Free software: BSD 3-Clause License
- Documentation: https://vulyk.readthedocs.org.

Overview
--------

We have a lot of tasks that can only be done manually.
Those includes digitizing of scanned assets declarations,
manual verification of results produced by different NLP software, stalking and so on.
So, we decided to generalize those tasks a bit and build a platform with basic support for crowdsourcing using
knowledge and chunks of code from the `unshred.it <http://unshred.it>`__
project. We don't use anything extraordinary: Flask, MongoDB, Bootstrap,
jQuery etc (all trademarks are the property of their respective owners,
don't forget that).

How it is built
--------------

Vulyk itself is a platform that can be stuffed with various plugins.

Vulyk is providing basic facilities to manage tasks, users, has simple but effective system of groups and permissions, also can load tasks in format of json lines and export results. For admin purposes we have a nice CLI tool that gives admin access to user management, task management, results management, stats, etc.

Vulyk is also doing dirty job to collect assets for plugin, to provide registration/login via social networks for end users and has leaderboard.


What for?
---------

-  digitize assets declarations of ukrainian officials for `Declarations project <http://declarations.com.ua>`__
-  improve the current state of Ukrainian NLP by creating a simple and
   robust solution for various NLP tasks that require human input.
-  process and manually verify existing results from
   morphological analyzer (by Andriy Rysin, Mariana Romanyshyn, et al.).
-  build tagged corpora of different kinds using manually processed
   results.
-  for the sake of The Great Justice of course!


What ships in the core repository
---------------------------------

We provide some kind of playground, where any interested (or
procrastination-addicted) person could spend some time crunching different tasks.
Site will show you, mr. Solver, some tasks of a given type, which you'll need to solve.

Leaderboard is already in place!

Some example task plugins live in separate repositories, for example
`vulyk-tagging <https://github.com/dchaplinsky/vulyk-tagging/>`__ and
`vulyk-declaration <https://github.com/dchaplinsky/vulyk-declaration>`__.

Local development
-----------------

Prerequisites:

- Python 3.10+
- ``uv``
- MongoDB available locally (the default settings expect ``localhost:27017``)
- at least one compatible Vulyk task plugin

Clone the repositories you need and install them into the same environment:

.. code:: bash

        git clone https://github.com/mrgambal/vulyk.git
        git clone https://github.com/dchaplinsky/vulyk-declaration.git
        git clone https://github.com/dchaplinsky/vulyk-tagging.git

        cd vulyk
        uv sync --dev
        uv pip install -e ../vulyk-declaration
        uv pip install -e ../vulyk-tagging

Then create ``local_settings.py`` in the project root. Vulyk will import it
after ``vulyk.settings``, so it is the easiest place to define local plugin and
deployment settings.

Minimal example:

.. code:: python


        # This one works for both, http://localhost:5000 and http://127.0.0.1:5000
        SOCIAL_AUTH_TWITTER_KEY = ''
        SOCIAL_AUTH_TWITTER_SECRET = ''

        # This one only works to log in via http://localhost:5000
        SOCIAL_AUTH_FACEBOOK_KEY = ''
        SOCIAL_AUTH_FACEBOOK_SECRET = ''

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

Core settings such as ``SECRET_KEY`` and the MongoDB connection may also come
from environment variables because ``vulyk.settings`` reads from ``os.environ``.

If you want to exercise the full browser login flow locally, configure at least
one supported social-auth provider in ``local_settings.py`` or your shell
environment.

Bootstrapping and running
-------------------------

Initialize the default group with the task types you want users to access:

.. code:: bash

        uv run manage.py init declaration_task tagging_task

Load task data from JSON Lines, ``.gz``, or ``.bz2`` files:

.. code:: bash

        uv run manage.py db load declaration_task --batch 01_declaration decl_tasks.jsonl
        uv run manage.py db load tagging_task --batch 01_tagging tagging_tasks.jsonl

Run the application:

.. code:: bash

        uv run manage.py run

The web UI will be available at ``http://localhost:5000`` by default.

Testing and documentation
-------------------------

The test suite uses ``unittest`` and expects MongoDB on ``localhost:27017``.
Tests override the database name to ``vulyk_test``.

.. code:: bash

        uv run -m unittest
        make coverage
        make docs

``make coverage`` generates ``htmlcov/index.html`` and ``coverage.xml``.
``make docs`` regenerates the Sphinx site under ``docs/_build/html``.

For plugin authoring details, see ``docs/plugins.rst``.
