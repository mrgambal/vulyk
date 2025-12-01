.PHONY: clean-pyc clean-build docs clean
LOGGING_LOCATION = /tmp/vulyk.log

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python; generates html and XML (coverage.xml) reports"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	uvx ruff check vulyk tests
	uvx ruff format vulyk tests

test:
	uv run -m unittest

test-all:
	tox

coverage:
	uv sync --dev && uv run coverage run -m unittest; rc=$$?; uv run coverage html || true; uv run coverage xml || true; open htmlcov/index.html || true; exit $$rc
	@# Confirm the XML report exists and show its path
	@test -f coverage.xml && echo "Generated: coverage.xml" || echo "coverage.xml not generated"

docs:
	rm -f docs/vulyk.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ vulyk
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	open docs/_build/html/index.html

release: clean
	uv publish

dist: clean
	uv build
	ls -l dist

pr: clean docs lint coverage
