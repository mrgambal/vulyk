#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""
import unittest

from vulyk import settings


class BaseTest(unittest.TestCase):
    settings.MONGODB_SETTINGS['DB'] = 'vulyk_test'


if __name__ == '__main__':
    unittest.main()
