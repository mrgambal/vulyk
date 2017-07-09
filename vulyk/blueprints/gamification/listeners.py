from vulyk.app import TASKS_TYPES
from vulyk.signals import on_task_done
from .models.task_types import AbstractGamifiedTaskType
from .core.events import Event


@on_task_done.connect
def track_events(sender, answer):
    task = answer.task
    batch = task.batch

    if not batch:
        return

    if not batch.task_type in TASKS_TYPES:
        return

    if isinstance(TASKS_TYPES[batch.task_type], AbstractGamifiedTaskType):
        # I'm going to operate!
        pass
