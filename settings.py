# coding=utf-8
import os

SECRET_KEY = 'random-secret-key'
SESSION_COOKIE_NAME = 'unshred_session'
DEBUG = True

MONGODB_SETTINGS = {
    'DB': os.environ.get("mongodb_db", "pullenti"),
    'HOST': os.environ.get("mongodb_host", "localhost"),
    'USERNAME': os.environ.get("mongodb_username", None),
    'PASSWORD': os.environ.get("mongodb_password", None),
    'PORT': (int(os.environ.get("mongodb_port"))
             if os.environ.get("mongodb_port") else None)
}

DEBUG_TB_INTERCEPT_REDIRECTS = False
SESSION_PROTECTION = 'strong'

SOCIAL_AUTH_STORAGE = 'social.apps.flask_app.me.models.FlaskStorage'
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

SOCIAL_AUTH_LOGIN_URL = '/'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'

SOCIAL_AUTH_USER_MODEL = 'models.user.User'
SOCIAL_AUTH_AUTHENTICATION_BACKENDS = (
    'social.backends.google.GoogleOAuth2',
    'social.backends.twitter.TwitterOAuth',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.vk.VKOAuth2',
)

# Keypairs for social auth backends
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_VK_OAUTH2_KEY = ''
SOCIAL_AUTH_VK_APP_SECRET = ''

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

JS_ASSETS = ['vendor/jquery/jquery.js',
             'vendor/jquery.cookie/jquery.cookie.js',
             'vendor/bootstrap/bootstrap.js',
             'vendor/jquery.hotkeys/jquery.hotkeys.js',
             'scripts/base.js']
JS_ASSETS_OUTPUT = 'scripts/packed.js'

JS_ASSETS_FILTERS = 'yui_js'

CSS_ASSETS = ['vendor/bootstrap/bootstrap.css',
              'styles/style.css']
CSS_ASSETS_OUTPUT = 'styles/packed.css'
CSS_ASSETS_FILTERS = 'yui_css'


# Default redundancy level for processing
USERS_PER_TASK = 2

# Restrict an access to site to admins only
SITE_IS_CLOSED = False


TASK_TYPES = [
    "tasks.dummy.DummyTaskType"
    # Or alternatively:
    # {
    #     "task": "tasks.dummy.DummyTaskType",
    #     "settings": {
    #         "redundancy": 5
    #     }
    # }
]
