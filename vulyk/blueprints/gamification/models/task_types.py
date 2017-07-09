from vulyk.models.task_types import AbstractTaskType


class AbstractGamifiedTaskType(AbstractTaskType):
    _task_type_meta = {
        "points_per_task": 1.0,
        "coins_per_task": 1.0
    }
