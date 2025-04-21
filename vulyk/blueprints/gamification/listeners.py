# coding=utf-8
from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal

from bson import ObjectId

from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractAnswer, Batch
from vulyk.signals import on_batch_done, on_task_done

from .core.events import Event
from .core.queries import MongoRuleExecutor
from .core.rules import Rule
from .core.state import UserState
from .models.events import EventModel
from .models.rules import ProjectAndFreeRules, RuleModel
from .models.state import UserStateModel
from .models.task_types import COINS_PER_TASK_KEY, POINTS_PER_TASK_KEY, AbstractGamifiedTaskType

__all__ = ["get_actual_rules", "track_events"]


@on_task_done.connect
def track_events(sender: object, answer: AbstractAnswer) -> None:
    """
    The most important gear of the gamification module.

    :param sender: Sender.
    :param answer: Current finished task's answer instance.

    """
    from vulyk.app import TASKS_TYPES
    from vulyk.blueprints.gamification import gamification

    user = answer.created_by
    batch = answer.task.batch

    if not batch or batch.task_type not in TASKS_TYPES:
        return

    if isinstance(TASKS_TYPES[batch.task_type], AbstractGamifiedTaskType):
        dt = datetime.now(timezone.utc)
        # I. Get current/new state
        state = UserStateModel.get_or_create_by_user(user)

        # II. gather earned goods
        badges = list(
            filter(
                lambda rule: MongoRuleExecutor.achieved(user_id=user.id, rule=rule, collection=WorkSession.objects),
                get_actual_rules(state=state, task_type_name=batch.task_type, now=dt),
            )
        )
        points = Decimal(batch.batch_meta[POINTS_PER_TASK_KEY])

        for b in badges:
            if b.bonus:
                points += b.bonus

        coins = Decimal(batch.batch_meta[COINS_PER_TASK_KEY])

        current_level = gamification.get_level(state.points)
        updated_level = gamification.get_level(state.points + points)

        # III. Alter the state and create event
        UserStateModel.update_state(
            diff=UserState(
                user=user,
                level=updated_level,
                points=points,
                actual_coins=Decimal(0),
                potential_coins=coins,
                achievements=badges,
                last_changed=dt,
            )
        )
        EventModel.from_event(
            Event.build(
                timestamp=dt,
                user=user,
                answer=answer,
                points_given=points,
                coins=coins,
                achievements=badges,
                acceptor_fund=None,
                level_given=None if current_level == updated_level else updated_level,
                viewed=False,
            )
        ).save()


def get_actual_rules(state: UserState, task_type_name: str, now: datetime) -> Iterator[Rule]:
    """
    Returns a list of eligible rules.

    :param state: Current state.
    :param task_type_name: The task's project.
    :param now: Timestamp to check for weekends.

    :return: Iterator of Rule instances.
    """
    return RuleModel.get_actual_rules(
        skip_ids=list(state.achievements.keys()),
        rule_filter=ProjectAndFreeRules(task_type_name),
        is_weekend=now.weekday() in [5, 6],
    )


@on_batch_done.connect
def materialize_coins(sender: Batch) -> None:
    """
    Convert potential coins to active ones for every member participated upon
    the batch in some gamified task type has been closed.

    :param sender: Batch that was closed.
    """
    from vulyk.app import TASKS_TYPES

    if sender.task_type not in TASKS_TYPES:
        return

    task_type = TASKS_TYPES[sender.task_type]

    if not isinstance(task_type, AbstractGamifiedTaskType):
        return

    coins = sender.batch_meta[COINS_PER_TASK_KEY]  # type: float
    # potentially expensive on memory
    task_ids = task_type.task_model.ids_in_batch(sender)  # type: List[str]
    # potentially expensive on memory/CPU (it isn't an generator or something)
    group_by_count = task_type.answer_model.answers_numbers_by_tasks(task_ids)  # type: Dict[ObjectId, int]

    # forgive me, Father, I have sinned so bad...
    for uid, freq in group_by_count.items():
        UserStateModel.transfer_coins_to_actual(uid=uid, amount=Decimal(freq * coins))
