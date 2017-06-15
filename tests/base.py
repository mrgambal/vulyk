#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import unittest

from mongoengine.connection import register_connection


class BaseTest(unittest.TestCase):
    MONGO_URI = 'mongodb://localhost:27017/'
    CONNECTION_NAME = 'default'

    register_connection(CONNECTION_NAME, name=CONNECTION_NAME, host=MONGO_URI)

    def setUp(self):
        pass

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
