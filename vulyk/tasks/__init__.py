from werkzeug.utils import import_string


def init_tasks(app):
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
