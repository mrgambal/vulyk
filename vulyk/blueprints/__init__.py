# -*- coding: utf-8 -*-
import flask

class VulykModule(flask.Blueprint):
    config = {}

    def configure(self, _config):
        self.config.update(_config)
