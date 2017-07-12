from datetime import datetime
from decimal import Decimal
from vulyk.signals import on_task_done
from .models.task_types import (
    AbstractGamifiedTaskType, COINS_PER_TASK_KEY, POINTS_PER_TASK_KEY)
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

        # state = state_model.to_state()
        state_model.actual_coins += Decimal(batch.batch_meta[COINS_PER_TASK_KEY])
        state_model.points += Decimal(batch.batch_meta[POINTS_PER_TASK_KEY])
        state_model.last_changed = dt

        # Apparently, it's not possible to update existing state when using
        # state_model = UserStateModel.from_state(state)
        state_model.save()

        ev = Event.build(
            timestamp=dt,
            user=user,
            answer=answer,
            points_given=batch.batch_meta[POINTS_PER_TASK_KEY],
            coins=batch.batch_meta[COINS_PER_TASK_KEY],
            achievements=[],
            acceptor_fund=None,
            level_given=None,
            viewed=False)

        EventModel.from_event(ev).save()
