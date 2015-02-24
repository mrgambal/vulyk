import json
import logging

from werkzeug.utils import import_string


logger = logging.getLogger(__name__)


def get_task(request):
    return json.dumps({})


def configure(self_settings):
    """
    Getting plugin's default settings, overwriting them with settings
    from local_settings.py, returns dict of settings
    """
    settings = {}
    try:
        local_settings = import_string('vulyk.local_settings')
        for attr in dir(self_settings):
            settings[attr] = getattr(self_settings, attr)
        for attr in dir(local_settings):
            if attr in dir(self_settings):
                settings[attr] = getattr(local_settings, attr)
    except Exception as e:
        logger.warning(e)

    return settings
