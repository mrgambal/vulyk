# -*- coding: utf-8 -*-
"""
"""
from ..base import BaseTest
from vulyk.blueprints.gamification import GamificationModule


class TestGetLevel(BaseTest):
    def setUp(self):
        super().setUp()

    def test_configured_levels(self):
        gamification = GamificationModule('gamification', __name__)
        levels = gamification.config["levels"]

        self.assertEqual(levels[1], 1)
        self.assertEqual(levels[2], 25)
        self.assertEqual(levels[3], 50)

    def test_configure(self):
        gamification = GamificationModule('gamification', __name__)
        gamification.configure({
            "levels": {
                1: 5,
                2: 10,
                3: 150
            }
        })
        levels = gamification.config["levels"]

        self.assertEqual(levels[1], 5)
        self.assertEqual(levels[2], 10)
        self.assertEqual(levels[3], 150)
        self.assertEqual(len(levels), 3)

    def test_get_default_levels(self):
        gamification = GamificationModule('gamification', __name__)

        self.assertEqual(gamification.get_level(0), 0)
        self.assertEqual(gamification.get_level(1), 1)
        self.assertEqual(gamification.get_level(2), 1)
        self.assertEqual(gamification.get_level(3), 1)
        self.assertEqual(gamification.get_level(24), 1)
        self.assertEqual(gamification.get_level(25), 2)
        self.assertEqual(gamification.get_level(26), 2)
        self.assertEqual(gamification.get_level(49), 2)
        self.assertEqual(gamification.get_level(50), 3)
        self.assertEqual(gamification.get_level(51), 3)
        self.assertEqual(gamification.get_level(5000), 50)

    def test_configured_get_levels(self):
        gamification = GamificationModule('gamification', __name__)
        gamification.configure({
            "levels": {
                1: 5,
                2: 10,
                3: 150
            }
        })
        levels = gamification.config["levels"]

        self.assertEqual(gamification.get_level(0), 0)
        self.assertEqual(gamification.get_level(4), 0)
        self.assertEqual(gamification.get_level(5), 1)
        self.assertEqual(gamification.get_level(9), 1)
        self.assertEqual(gamification.get_level(10), 2)
