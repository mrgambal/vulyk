import json

from werkzeug.utils import import_string


def get_task(request):
    return json.dumps({})


def configure(self_settings):
    """
    Getting plugin's default settings, overwriting them with settings
    from local_settings.py, returns list of settings
    """
    try:
        local_settings = import_string('vulyk.local_settings')
        for attr in dir(local_settings):
            if attr in dir(self_settings):
                self_settings[attr] = getattr(local_settings, attr)
    except:
        pass

    return self_settings
