#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import unittest
import mongomock

from mongoengine.connection import register_connection


class BaseTest(unittest.TestCase):
    def setUp(self):
        register_connection('default', name='default')

    def tearDown(self):
        pass


class MongoTestHelpers:
    collection = mongomock.MongoClient().db.collection

    @staticmethod
    def connection(alias):
        return {alias: MongoTestHelpers.collection}


if __name__ == '__main__':
    unittest.main()
