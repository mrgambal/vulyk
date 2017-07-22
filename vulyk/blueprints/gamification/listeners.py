# coding=utf-8
from collections import Iterator
from datetime import datetime
from decimal import Decimal

from vulyk.models.stats import WorkSession
from vulyk.signals import on_task_done

from .core.events import Event
from .core.queries import MongoRuleExecutor
from .core.state import UserState
from .models.events import EventModel
from .models.rules import RuleModel, ProjectAndFreeRules
from .models.state import UserStateModel
from .models.task_types import (
    AbstractGamifiedTaskType, COINS_PER_TASK_KEY, POINTS_PER_TASK_KEY)

__all__ = [
    'track_events',
    'get_actual_rules'
]


@on_task_done.connect
def track_events(sender, answer) -> None:
    """
    The most important gear of the gamification module.

    :param sender: Sender
    :type sender: object
    :param answer: Current finished task's answer instance
    :type answer: AbstractAnswer

    :rtype: None
    """
    from vulyk.app import TASKS_TYPES
    from vulyk.blueprints.gamification import gamification

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
                task_type_name=batch.task_type,
                now=dt)))
        points = batch.batch_meta[POINTS_PER_TASK_KEY]
        coins = batch.batch_meta[COINS_PER_TASK_KEY]

        # III. Alter the state and create event
        UserStateModel.update_state(
            diff=UserState(
                user=user,
                level=0,
                points=Decimal(points),
                actual_coins=Decimal(coins),
                potential_coins=Decimal(),
                achievements=badges,
                last_changed=dt))
        EventModel.from_event(
            Event.build(
                timestamp=dt,
                user=user,
                answer=answer,
                points_given=points,
                coins=coins,
                achievements=badges,
                acceptor_fund=None,
                level_given=None,
                viewed=False)
        ).save()


def get_actual_rules(
    state: UserState,
    task_type_name: str,
    now: datetime
) -> Iterator:
    """
    Returns a list of eligible rules.

    :param state: Current state
    :type state: UserState
    :param task_type_name: The task's project
    :type task_type_name: str
    :param now: Timestamp to check for weekends
    :type now: datetime

    :return: Iterator of Rule instances
    :rtype: Iterator[vulyk.blueprints.gamification.core.rules.Rule]
    """
    return RuleModel.get_actual_rules(
        skip_ids=list(state.achievements.keys()),
        rule_filter=ProjectAndFreeRules(task_type_name),
        is_weekend=now.weekday() in [5, 6])
