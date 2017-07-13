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

    user = answer.created_by
    batch = answer.task.batch

    if not batch or batch.task_type not in TASKS_TYPES:
        return

    if isinstance(TASKS_TYPES[batch.task_type], AbstractGamifiedTaskType):
        dt = datetime.now()  # TODO: TZ Aware?
        # I. Get current/new state
        state = UserStateModel.get_or_create_by_user(user)

        # II. gather earned goods
        badges = list(filter(
            lambda rule: MongoRuleExecutor.achieved(
                user_id=user.id,
                rule=rule,
                collection=WorkSession.objects),
            get_actual_rules(
                state=state,
                batch_name=batch.id,
                now=dt)))
        # III. Alter the state and create event

        UserStateModel.update_state(
            diff=UserState(
                user=user,
                level=0,
                points=Decimal(batch.batch_meta[POINTS_PER_TASK_KEY]),
                actual_coins=Decimal(batch.batch_meta[COINS_PER_TASK_KEY]),
                potential_coins=Decimal(),
                achievements=badges,
                last_changed=dt))
        EventModel.from_event(
            Event.build(
                timestamp=dt,
                user=user,
                answer=answer,
                points_given=batch.batch_meta[POINTS_PER_TASK_KEY],
                coins=batch.batch_meta[COINS_PER_TASK_KEY],
                achievements=badges,
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
