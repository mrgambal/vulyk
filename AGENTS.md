# Vulyk

## Commands

Run commands from the repository root. `uv` manages the `.venv` environment.

```sh
# Install development dependencies and the project
make dev

# Run the test suite
make test

# Check lint without applying formatting
uv ruff check vulyk tests

# Generate documentation
make docs

# Run the local application (MongoDB and compatible task plugins required)
uv run manage.py run
```

`make lint` also runs `ruff format`, which changes files; use it only when formatting is intended. Tests use the `vulyk_test` MongoDB database. See `docs/installation.rst` and `docs/usage.rst` for setup and CLI workflows.

## Configuration and compatibility

- `local_settings.py` loads after `vulyk.settings`; use it for local MongoDB and plugin settings, and keep it untracked because it may contain credentials.
- MongoDB is required for application and test runs. Tests use the `vulyk_test` database.
- `vulyk/social_storage.py` owns default social-auth storage. Its nonce upsert replaces stale `social-storage-mongoengine` code that calls removed `get_or_create()` and requires the unique compound index. Do not bypass this workaround or edit installed packages.
- Install task plugins separately when needed. Do not commit machine-specific sibling path dependencies.

## Working conventions

- Use type hints, reST-style docstrings for public methods, and punctuated comments.
- The shell is Fish. Activate `.venv` before commands, or call tools through `.venv/bin/` explicitly.
- Use Context7 for current library documentation and Serena for precise code navigation when available.


## Project boundaries

- Vulyk is a Flask crowdsourcing platform with MongoDB, CLI management, social login, optional gamification, and pluggable task workflows. Keep task-specific behavior in compatible plugins where the existing plugin interface supports it; do not assume a task type is built into the core.
- Do not commit credentials, passwords, tokens, connection strings, or other secrets. Keep local configuration and downloaded data out of commits.
- Avoid adding dependencies unless the task requires them; dependencies and development tools are declared in `pyproject.toml` and managed with `uv`.

## Completion

- Keep changes limited to the requested behavior and follow nearby code and test patterns.
- Run the targeted tests and relevant checks for changed code; report checks that could not be run.
- Update relevant documentation when behavior, setup, or CLI usage changes.
- Do not modify generated documentation output in `docs/_build/`; regenerate it with `make docs` when needed.
