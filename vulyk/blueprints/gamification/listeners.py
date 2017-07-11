from datetime import datetime
from vulyk.signals import on_task_done
from .models.task_types import AbstractGamifiedTaskType
from .core.events import Event
from .core.state import UserState
from .models.state import UserStateModel
from .models.events import EventModel


@on_task_done.connect
def track_events(sender, answer):
    from vulyk.app import TASKS_TYPES

    task = answer.task
    user = answer.created_by
    batch = task.batch

    if not batch:
        return

    if not batch.task_type in TASKS_TYPES:
        return

    if isinstance(TASKS_TYPES[batch.task_type], AbstractGamifiedTaskType):
        dt = datetime.now()  # TODO: TZ Aware?
        try:
            state_model = UserStateModel.objects.get(user=user)
        except UserStateModel.DoesNotExist:
            state_model = UserStateModel.objects.create(user=user)

        state = state_model.to_state()
        state.actual_coins += batch.meta["coins_per_task"]
        state.points += batch.meta["points_per_task"]
        state.last_changed = dt

        UserStateModel.from_state(state).save()

        ev = Event.build(
            timestamp=dt,
            user=user,
            answer=answer,
            points_given=batch.meta["points_per_task"],
            coins=batch.meta["coins_per_task"],
            achievements=[],
            acceptor_fund=None,
            level_given=None,
            viewed=False)

        EventModel.from_event(ev).save()
