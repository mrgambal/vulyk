# -*- coding=utf-8 -*-
import logging
import os
from typing import Any

ENV = os.environ.get


SECRET_KEY: str = ENV("SECRET_KEY", "random-secret-key")
SESSION_COOKIE_NAME: str = ENV("SESSION_COOKIE_NAME", "vulyk_session")
DEBUG: bool = ENV("DEBUG", default=True) in ("true", "t", "1", True)

MONGODB_SETTINGS: dict[str, str | int | None] = {
    "DB": ENV("mongodb_db", "vulyk"),
    "HOST": ENV("mongodb_host", "localhost"),
    "USERNAME": ENV("mongodb_username", None),
    "PASSWORD": ENV("mongodb_password", None),
    "PORT": int(str(ENV("mongodb_port"))) if ENV("mongodb_port") else None,
}

DEBUG_TB_INTERCEPT_REDIRECTS: bool = ENV("DEBUG_TB_INTERCEPT_REDIRECTS", default=False) in ("true", "t", "1", True)
SESSION_PROTECTION: str = ENV("SESSION_PROTECTION", "strong")

LOG_TO_STDERR: bool = ENV("LOG_TO_FILE", "False").lower() in ("true", "t", "1")
LOGGING_LOCATION: str = ENV("LOGGING_LOCATION", "/var/log/vulyk/app.log")
LOGGING_FORMAT: str = ENV("LOGGING_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOGGING_LEVEL: int = logging.DEBUG if DEBUG else logging.INFO
LOGGING_MAX_FILE_BYTES: int = int(ENV("LOGGING_MAX_FILE_BYTES", 10 * 1024 * 1024))

SOCIAL_AUTH_STORAGE: str = ENV("SOCIAL_AUTH_STORAGE", "social_flask_mongoengine.models.FlaskStorage")
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL: bool = ENV("SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL", default=True) in (
    "true",
    "t",
    "1",
    True,
)

SOCIAL_AUTH_LOGIN_URL: str = ENV("SOCIAL_AUTH_LOGIN_URL", "/")
SOCIAL_AUTH_LOGIN_REDIRECT_URL: str = ENV("SOCIAL_AUTH_LOGIN_REDIRECT_URL", "/")

SOCIAL_AUTH_USER_MODEL: str = ENV("SOCIAL_AUTH_USER_MODEL", "vulyk.models.user.User")
SOCIAL_AUTH_AUTHENTICATION_BACKENDS: tuple[str, ...] = tuple(
    ENV(
        "SOCIAL_AUTH_AUTHENTICATION_BACKENDS",
        (
            "social_core.backends.google.GoogleOAuth2",
            "social_core.backends.twitter.TwitterOAuth",
            "social_core.backends.facebook.FacebookOAuth2",
        ),
    )
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY: str = ENV("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: str = ENV("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")

SOCIAL_AUTH_TWITTER_KEY: str = ENV("SOCIAL_AUTH_TWITTER_KEY", "")
SOCIAL_AUTH_TWITTER_SECRET: str = ENV("SOCIAL_AUTH_TWITTER_SECRET", "")

SOCIAL_AUTH_FACEBOOK_KEY: str = ENV("SOCIAL_AUTH_FACEBOOK_KEY", "")
SOCIAL_AUTH_FACEBOOK_SECRET: str = ENV("SOCIAL_AUTH_FACEBOOK_SECRET", "")


def _ensure_list(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [value]


SOCIAL_AUTH_FACEBOOK_SCOPE: list[str] = _ensure_list(ENV("SOCIAL_AUTH_FACEBOOK_SCOPE", ["email"]))

STATIC_FOLDER: str = "static"
JS_ASSETS: list[str] = [
    "vendor/jquery/jquery.js",
    "vendor/jquery.cookie/jquery.cookie.js",
    "vendor/bootstrap/bootstrap.js",
    "vendor/jquery.hotkeys/jquery.hotkeys.js",
    "vendor/jquery.magnific-popup/jquery.magnific-popup.js",
    "scripts/base.js",
]
JS_ASSETS_OUTPUT: str = ENV("JS_ASSETS_OUTPUT", "scripts/packed.js")

JS_ASSETS_FILTERS: str = ENV("JS_ASSETS_FILTERS", "rjsmin")

CSS_ASSETS: list[str] = [
    "vendor/bootstrap/bootstrap.css",
    "vendor/jquery.magnific-popup/jquery.magnific-popup.css",
    "styles/style.css",
]
CSS_ASSETS_OUTPUT: str = ENV("CSS_ASSETS_OUTPUT", "styles/packed.css")
CSS_ASSETS_FILTERS: str = ENV("CSS_ASSETS_FILTERS", "rcssmin")
# static files for plugin X get stored in COLLECT_STATIC_ROOT/plugin_X/static
COLLECT_PLUGIN_DIR_PREFIX: str = "plugin_"

# Default redundancy level for processing
USERS_PER_TASK: int = int(ENV("USERS_PER_TASK", "2"))

# Restrict an access to site to admins only
SITE_IS_CLOSED: bool = bool(ENV("SITE_IS_CLOSED", default=False))

ENABLED_TASKS: dict[str, Any] = ENV("ENABLED_TASKS", {})

SITE_NAME: str = "Vulyk workspace"
SITE_MOTTO: str = "Vulyk: crowdsourcing platform"

DEFAULT_BATCH: str = "default"

WARM_WELCOME: str = """
<h3>Вас вітає Канцелярська сотня.</h3>
"""

SITE_LOGO: str = ENV("SITE_LOGO", "/static/images/logo.png")
SITE_TITLE: str = ENV("SITE_TITLE", "Канцелярська сотня представляет!")

TEMPLATE_BASE_FOLDERS: list[str] = []
TEMPLATES_FOLDER: str = "templates"

THANKS_TASK_MESSAGE: str = "Дякуємо за допомогу!"

ENABLED_BLUEPRINTS: list[dict[str, str | dict | None]] = [
    {"path": "vulyk.blueprints.gamification.gamification", "config": {}, "url_prefix": "gamification"}
]

ENABLE_ADMIN: bool = False
REDIRECT_USER_AFTER_LOGIN: bool = True
