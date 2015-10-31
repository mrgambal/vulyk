#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""

import unittest
import mongomock

from mongoengine.connection import register_connection


_collection = mongomock.MongoClient().db.collection


def mocked_get_connection(alias):
    return {alias: _collection}


class BaseTest(unittest.TestCase):

    def setUp(self):
        register_connection('default', name='default')

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
