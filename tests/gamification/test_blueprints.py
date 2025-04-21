# -*- coding: utf-8 -*-
""" """

import unittest

import flask

from vulyk.blueprints import VulykModule
from vulyk.blueprints.gamification import GamificationModule

from ..base import BaseTest


class TestGetLevel(BaseTest):
    def test_configured_levels(self):
        gamification = GamificationModule("gamification", __name__)
        levels = gamification.config["levels"]

        self.assertEqual(levels[1], 1)
        self.assertEqual(levels[2], 25)
        self.assertEqual(levels[3], 50)

    def test_configure(self):
        gamification = GamificationModule("gamification", __name__)
        gamification.configure({"levels": {1: 5, 2: 10, 3: 150}})
        levels = gamification.config["levels"]

        self.assertEqual(levels[1], 5)
        self.assertEqual(levels[2], 10)
        self.assertEqual(levels[3], 150)
        self.assertEqual(len(levels), 3)

    def test_get_default_levels(self):
        gamification = GamificationModule("gamification", __name__)

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
        gamification = GamificationModule("gamification", __name__)
        gamification.configure({"levels": {1: 5, 2: 10, 3: 150}})

        self.assertEqual(gamification.get_level(0), 0)
        self.assertEqual(gamification.get_level(4), 0)
        self.assertEqual(gamification.get_level(5), 1)
        self.assertEqual(gamification.get_level(9), 1)
        self.assertEqual(gamification.get_level(10), 2)

    def test_context_filler(self):
        class TestModule(VulykModule):
            pass

        app = flask.Flask("test")
        app.config.from_object("vulyk.settings")
        test_module = TestModule("test_module", __name__)
        test_module.add_context_filler(lambda: {"x": "you speak"})
        test_module.add_context_filler(lambda: {"y": "bollocks"})

        def fake_route():
            template = "{{test_module_x}} {{test_module_y}}"

            return flask.render_template_string(template)

        test_module.route("/test", methods=["GET"])(fake_route)
        app.register_blueprint(test_module)
        resp = app.test_client().get("/test")

        self.assertEqual(resp.data.decode("utf8"), "you speak bollocks")


if __name__ == "__main__":
    unittest.main()
