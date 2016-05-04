#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pip.req import parse_requirements


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

install_reqs = parse_requirements('requirements.txt', session=uuid.uuid1())

requirements = [str(ir.req) for ir in install_reqs]
test_requirements = requirements

setup(
    name='vulyk',
    version='0.3.1',
    description='Crowdsourcing platform for different kinds of tasks',
    long_description=readme + '\n\n' + history,
    author='Dmytro Hambal',
    author_email='mr_gambal@outlook.com',
    url='https://github.com/mrgambal/vulyk',
    packages=[
        'vulyk',
        'vulyk.cli',
        'vulyk.ext',
        'vulyk.models',
        'vulyk.tasks'
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    scripts=['manage.py']
)
