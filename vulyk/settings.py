# -*- coding=utf-8 -*-
import os
import logging

ENV = os.environ.get

SECRET_KEY = ENV('SECRET_KEY', 'random-secret-key')
SESSION_COOKIE_NAME = ENV('SESSION_COOKIE_NAME', 'vulyk_session')
DEBUG = ENV('DEBUG', True)

MONGODB_SETTINGS = {
    'DB': ENV('mongodb_db', 'vulyk'),
    'HOST': ENV('mongodb_host', 'localhost'),
    'USERNAME': ENV('mongodb_username', None),
    'PASSWORD': ENV('mongodb_password', None),
    'PORT': (int(ENV('mongodb_port'))
             if ENV('mongodb_port') else None)
}

DEBUG_TB_INTERCEPT_REDIRECTS = ENV('DEBUG_TB_INTERCEPT_REDIRECTS', False)
SESSION_PROTECTION = ENV('SESSION_PROTECTION', 'strong')

LOGGING_LOCATION = ENV('LOGGING_LOCATION', '/var/log/vulyk/app.log')
LOGGING_FORMAT = ENV('LOGGING_FORMAT',
                     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGGING_MAX_FILE_BYTES = ENV('LOGGING_MAX_FILE_BYTES', 10 * 1024 * 1024)

SOCIAL_AUTH_STORAGE = ENV('SOCIAL_AUTH_STORAGE',
                          'social_flask_mongoengine.models.FlaskStorage')
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = ENV('SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL',
                                         True)

SOCIAL_AUTH_LOGIN_URL = ENV('SOCIAL_AUTH_LOGIN_URL', '/')
SOCIAL_AUTH_LOGIN_REDIRECT_URL = ENV('SOCIAL_AUTH_LOGIN_REDIRECT_URL', '/')

SOCIAL_AUTH_USER_MODEL = ENV('SOCIAL_AUTH_USER_MODEL',
                             'vulyk.models.user.User')
SOCIAL_AUTH_AUTHENTICATION_BACKENDS = ENV(
    'SOCIAL_AUTH_AUTHENTICATION_BACKENDS', (
        'social_core.backends.google.GoogleOAuth2',
        'social_core.backends.twitter.TwitterOAuth',
        'social_core.backends.facebook.FacebookOAuth2'
    ))

# Keypairs for social auth backends
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ENV('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ENV('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

SOCIAL_AUTH_TWITTER_KEY = ENV('SOCIAL_AUTH_TWITTER_KEY', '')
SOCIAL_AUTH_TWITTER_SECRET = ENV('SOCIAL_AUTH_TWITTER_SECRET', '')

SOCIAL_AUTH_FACEBOOK_KEY = ENV('SOCIAL_AUTH_FACEBOOK_KEY', '')
SOCIAL_AUTH_FACEBOOK_SECRET = ENV('SOCIAL_AUTH_FACEBOOK_SECRET', '')

SOCIAL_AUTH_VK_OAUTH2_KEY = ENV('SOCIAL_AUTH_VK_OAUTH2_KEY', '')
SOCIAL_AUTH_VK_APP_SECRET = ENV('SOCIAL_AUTH_VK_APP_SECRET', '')

SOCIAL_AUTH_FACEBOOK_SCOPE = ENV('SOCIAL_AUTH_FACEBOOK_SCOPE', ['email'])

STATIC_FOLDER = "static"
JS_ASSETS = ['vendor/jquery/jquery.js',
             'vendor/jquery.cookie/jquery.cookie.js',
             'vendor/bootstrap/bootstrap.js',
             'vendor/jquery.hotkeys/jquery.hotkeys.js',
             'vendor/jquery.magnific-popup/jquery.magnific-popup.js',
             'scripts/base.js']
JS_ASSETS_OUTPUT = ENV('JS_ASSETS_OUTPUT', 'scripts/packed.js')

JS_ASSETS_FILTERS = ENV('JS_ASSETS_FILTERS', 'rjsmin')

CSS_ASSETS = ['vendor/bootstrap/bootstrap.css',
              'vendor/jquery.magnific-popup/jquery.magnific-popup.css',
              'styles/style.css']
CSS_ASSETS_OUTPUT = ENV('CSS_ASSETS_OUTPUT', 'styles/packed.css')
CSS_ASSETS_FILTERS = ENV('CSS_ASSETS_FILTERS', 'cssmin')
# static files for plugin X get stored in COLLECT_STATIC_ROOT/plugin_X/static
COLLECT_PLUGIN_DIR_PREFIX = 'plugin_'

# Default redundancy level for processing
USERS_PER_TASK = ENV('USERS_PER_TASK', 2)

# Restrict an access to site to admins only
SITE_IS_CLOSED = ENV('SITE_IS_CLOSED', False)

ENABLED_TASKS = ENV('ENABLED_TASKS', {})

SITE_NAME = 'Vulyk workspace'
SITE_MOTTO = 'Vulyk: crowdsourcing platform'

DEFAULT_BATCH = 'default'

WARM_WELCOME = """
<h3>Вас вітає Канцелярська сотня.</h3>
"""

SITE_LOGO = ENV('SITE_LOGO', '/static/images/logo.png')
SITE_TITLE = ENV('SITE_TITLE', 'Канцелярская сотня представляет!')

TEMPLATE_BASE_FOLDERS = []
TEMPLATES_FOLDER = "templates"

THANKS_TASK_MESSAGE = 'Спасибо за помощь, сознательный гражданин!'

ENABLED_BLUEPRINTS = [
    {
        "path": "vulyk.blueprints.gamification.gamification",
        "config": {},
        "url_prefix": "gamification"
    }
]
