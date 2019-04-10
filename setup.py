#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

with open('requirements.txt', 'r') as fd:
    requirements = list(
        filter(lambda r: not r.strip().startswith('#'), fd.readlines())
    )

test_requirements = requirements

setup(
    name='vulyk',
    version='0.5.1',
    description='Crowdsourcing platform for different kinds of tasks',
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    author='Dmytro Hambal',
    author_email='mr_hambal@outlook.com',
    url='https://github.com/mrgambal/vulyk',
    packages=[
        'vulyk',
        'vulyk.admin',
        'vulyk.blueprints',
        'vulyk.blueprints.gamification',
        'vulyk.blueprints.gamification.core',
        'vulyk.blueprints.gamification.models',
        'vulyk.bootstrap',
        'vulyk.cli',
        'vulyk.admin',
        'vulyk.ext',
        'vulyk.models'
    ],
    package_dir={'vulyk': 'vulyk'},
    include_package_data=True,
    install_requires=requirements,
    license='BSD',
    zip_safe=False,
    keywords='vulyk',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    scripts=['manage.py']
)
