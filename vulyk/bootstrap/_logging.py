# -*- coding: utf-8 -*-
"""
Project-wide logger configuration.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask

__all__ = ["init_logger"]


def init_logger(app: Flask) -> None:
    """
    Initialize the logging system.

    :param app: Current Flask application.
    """

    if app.config["LOG_TO_STDERR"]:
        handler = logging.StreamHandler()
    else:
        filename = app.config["LOGGING_LOCATION"]
        # Try to ensure the directory exists. If we fail (e.g., due to permissions),
        # fall back to stderr handler so initialization doesn't crash tests.
        try:
            dirname = os.path.dirname(filename) or "."
            os.makedirs(dirname, exist_ok=True)
            handler = RotatingFileHandler(filename=filename, maxBytes=app.config["LOGGING_MAX_FILE_BYTES"])
        except OSError:
            # Directory creation or file open failed (e.g. permission issues)
            handler = logging.StreamHandler()

    handler.setLevel(app.config["LOGGING_LEVEL"])
    handler.setFormatter(logging.Formatter(app.config["LOGGING_FORMAT"]))

    app.logger.addHandler(handler)
    app.logger.debug("Logging system has been initialized successfully.")
