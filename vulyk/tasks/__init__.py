from werkzeug.utils import import_string


def init_tasks(app):
    """
    Extracts modules (task types) from global configuration

    :param app: Current Flask application instance
    :type app: Flask

    :return: Dictionary with instantiated *TaskType objects
    :rtype: dict
    """
    task_types = {}

    for tt in app.config.get("TASK_TYPES", []):
        settings = {
            "redundancy": app.config["USERS_PER_TASK"]
        }

        if isinstance(tt, dict):
            tt = tt["task"]
            settings.update(tt.get("settings", {}))

        task_type = import_string(tt)(**settings)
        task_types[task_type.type_name] = task_type

    return task_types
