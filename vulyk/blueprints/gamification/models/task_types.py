from vulyk.models.task_types import AbstractTaskType

POINTS_PER_TASK_KEY = "points_per_task"
COINS_PER_TASK_KEY = "coins_per_task"


class AbstractGamifiedTaskType(AbstractTaskType):
    _task_type_meta = {
        POINTS_PER_TASK_KEY: 1.0,
        COINS_PER_TASK_KEY: 1.0
    }
