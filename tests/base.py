#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import unittest
import mongomock

from mongoengine.connection import register_connection, disconnect


class BaseTest(unittest.TestCase):
    def setUp(self):
        register_connection('default', name='default')

    def tearDown(self):
        disconnect('default')


class DBTestHelpers:
    collections = mongomock.MongoClient().db.collection

    @staticmethod
    def connection(alias):
        return {alias: DBTestHelpers.collections}


if __name__ == '__main__':
    unittest.main()
