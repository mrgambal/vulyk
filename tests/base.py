#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""

import unittest

from mongoengine.connection import register_connection

from vulyk import settings


class BaseTest(unittest.TestCase):
    DB_NAME = "vulyk_test"
    MONGO_URI = "mongodb://localhost:27017/"
    # override to run against test DB during tests
    settings.MONGODB_SETTINGS["DB"] = DB_NAME
    # allows us to run selected tests w/o need to launch the whole bunch
    register_connection("default", name=DB_NAME, host=MONGO_URI)


if __name__ == "__main__":
    unittest.main()
