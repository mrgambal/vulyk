#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pathlib

from setuptools import find_packages, setup

base_dir = pathlib.Path(__file__).parent
readme = (base_dir / "README.rst").read_text()
history = (base_dir / "HISTORY.rst").read_text().replace('.. :changelog:', '')
requirements = []

with open('requirements.txt', 'r') as fd:
    requirements = [line for line in fd if not line.strip().startswith("#")]

setup(
    name='vulyk',
    version='0.5.2',
    description='Crowdsourcing platform for different kinds of tasks',
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    author='Dmytro Hambal',
    author_email='mr_hambal@outlook.com',
    url='https://github.com/mrgambal/vulyk',
    packages=find_packages(),
    package_dir={'vulyk': 'vulyk'},
    include_package_data=True,
    install_requires=requirements,
    extras_require={"dev": ["coverage", "mongomock", "wheel"]},
    license='BSD',
    zip_safe=False,
    keywords='vulyk',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    test_suite='tests',
    scripts=['manage.py']
)
