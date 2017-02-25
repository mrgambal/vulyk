#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import mongomock
import unittest

from mongoengine.connection import register_connection


class BaseTest(unittest.TestCase):
    def setUp(self):
        register_connection('default', name='default')

    def tearDown(self):
        pass


class DBTestHelpers:
    collections = mongomock.MongoClient().db.collection

    @staticmethod
    def dereference(this, value):
        """
        Hack for mongomock collection that cannot deal with ReferenceField

        :type this: mongomock.collection.Collection
        :type value: bson.DBRef

        :rtype: mongoengine.document.Document | None
        """
        return this[value.collection].find_one(value.id)

    @classmethod
    def connection(cls, alias):
        """
        :type alias: str
        """
        mongomock.collection.Collection.dereference = cls.dereference

        return {alias: cls.collections}


if __name__ == '__main__':
    unittest.main()
