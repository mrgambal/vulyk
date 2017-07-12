# coding=utf-8
from datetime import datetime
from decimal import Decimal

from vulyk.models.stats import WorkSession
from vulyk.signals import on_task_done

from .core.events import Event
from .core.queries import MongoRuleExecutor
from .core.state import UserState
from .models.events import EventModel
from .models.rules import RuleModel
from .models.state import UserStateModel
from .models.task_types import (
    AbstractGamifiedTaskType, COINS_PER_TASK_KEY, POINTS_PER_TASK_KEY)

__all__ = [
    'track_events'
    'get_actual_rules'
]


@on_task_done.connect
def track_events(sender, answer) -> None:
    """
    The most important gear of the gamification module.

    :param sender:
    :type sender:
    :param answer: Current finished task's answer instance
    :type answer: AbstractAnswer

    :rtype: None
    """
    from vulyk.app import TASKS_TYPES

    task = answer.task
    user = answer.created_by
    batch = task.batch

    if not batch or batch.task_type not in TASKS_TYPES:
        return

    if isinstance(TASKS_TYPES[batch.task_type], AbstractGamifiedTaskType):
        dt = datetime.now()  # TODO: TZ Aware?
        # I. Get current/new state
        try:
            state_model = UserStateModel.objects.get(user=user)
        except UserStateModel.DoesNotExist:
            state_model = UserStateModel.objects.create(user=user)

        # II. gather earned goods
        rules = list(filter(
            lambda rule: MongoRuleExecutor.achieved(
                user_id=user.id,
                rule=rule,
                collection=WorkSession.objects),
            get_actual_rules(
                state=state_model.to_state(),
                batch_name=batch.id,
                now=dt)))
        coins_earned = Decimal(batch.batch_meta[COINS_PER_TASK_KEY])
        points_earned = Decimal(batch.batch_meta[POINTS_PER_TASK_KEY])
        # TODO: add USM.update_from_state(state) method, save progress
        # III. Alter the state and create event
        state_model.actual_coins += coins_earned
        state_model.points += points_earned
        state_model.last_changed = dt

        state_model.save()

        EventModel.from_event(
            Event.build(
                timestamp=dt,
                user=user,
                answer=answer,
                points_given=batch.batch_meta[POINTS_PER_TASK_KEY],
                coins=batch.batch_meta[COINS_PER_TASK_KEY],
                achievements=rules,
                acceptor_fund=None,
                level_given=None,
                viewed=False)
        ).save()


def get_actual_rules(state: UserState, batch_name: str, now: datetime) -> list:
    """

    :param state:
    :type state:
    :param batch_name:
    :type batch_name:
    :param now:
    :type now:

    :return:
    :rtype:
    """
    return RuleModel.get_actual_rules(
        ids=list(state.achievements.keys()),
        batch_name=batch_name,
        is_weekend=now.weekday() in [5, 6])
