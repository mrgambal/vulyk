# -*- coding: utf-8 -*-
"""
Project-wide logger configuration.
"""
import logging
from logging.handlers import RotatingFileHandler, StreamHandler

__all__ = [
    'init_logger'
]


def init_logger(app):
    """
    :param app: Current Flask application
    :type app: flask.Flask 
    """

    if app.config['LOG_TO_STDERR']:
        handler = StreamHandler()
    else:
        handler = RotatingFileHandler(
            filename=app.config['LOGGING_LOCATION'],
            maxBytes=app.config['LOGGING_MAX_FILE_BYTES']
        )

    handler.setLevel(app.config['LOGGING_LEVEL'])
    handler.setFormatter(logging.Formatter(app.config['LOGGING_FORMAT']))

    app.logger.addHandler(handler)
    app.logger.debug('Logging system has been initialized successfully.')
