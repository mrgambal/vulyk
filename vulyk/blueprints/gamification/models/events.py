# -*- coding: utf-8 -*-
"""
Contains all DB models related to game events.
"""
from collections import Iterator

from flask_mongoengine import Document
from mongoengine import (
    DecimalField, ComplexDateTimeField, ReferenceField, BooleanField,
    ListField, IntField, Q
)

from vulyk.models.tasks import AbstractAnswer
from vulyk.models.user import User

from .foundations import FundModel
from .rules import RuleModel
from ..core.events import Event

__all__ = [
    'EventModel'
]


class EventModel(Document):
    """
    Database-specific gamification system event representation
    """
    timestamp = ComplexDateTimeField(required=True)
    user = ReferenceField(
        document_type=User, db_field='user', required=True)
    answer = ReferenceField(
        document_type=AbstractAnswer, db_field='answer', required=False)
    # points must only be added
    points_given = DecimalField(min_value=0, required=True, db_field='points')
    # coins can be both given and withdrawn
    coins = DecimalField(required=True)
    achievements = ListField(
        field=ReferenceField(document_type=RuleModel, required=False))
    # if user donates earned coins to a fund, specify the fund
    acceptor_fund = ReferenceField(
        document_type=FundModel, required=False, db_field='acceptorFund')
    level_given = IntField(min_value=1, required=False, db_field='level')
    # has user seen an update or not
    viewed = BooleanField(default=False)

    meta = {
        'collection': 'gamification.events',
        'allow_inheritance': True,
        'indexes': [
            'user',
            {
                'fields': ['answer'],
                'unique': True,
                'sparse': True
            },
            'acceptor_fund',
            'timestamp'
        ]
    }

    def to_event(self) -> Event:
        """
        DB-specific model to Event converter.

        :return: New Event instance
        :rtype: Event
        """
        return Event.build(
            timestamp=self.timestamp,
            user=self.user,
            answer=self.answer,
            points_given=self.points_given,
            coins=self.coins,
            achievements=[a.to_rule() for a in self.achievements if hasattr(a, "to_rule")],
            acceptor_fund=None
            if self.acceptor_fund is None
            else self.acceptor_fund.to_fund(),
            level_given=self.level_given,
            viewed=self.viewed
        )

    @classmethod
    def from_event(cls: type, event: Event):
        """
        Event to DB-specific model converter.

        :param event: Source event instance
        :type event: Event

        :return: New full-bodied model instance
        :rtype: EventModel
        """
        return cls(
            timestamp=event.timestamp,
            user=event.user,
            answer=event.answer,
            points_given=event.points_given,
            coins=event.coins,
            achievements=RuleModel.objects(
                id__in=[r.id for r in event.achievements]),
            acceptor_fund=None
            if event.acceptor_fund is None
            else FundModel.objects.get(id=event.acceptor_fund.id),
            level_given=event.level_given,
            viewed=event.viewed
        )

    @classmethod
    def get_unread_events(cls, user: User) -> Iterator:
        """
        Returns aggregated and sorted list of generator (achievements & level-ups)
        user'd been given but hasn't checked yet.

        :param user: The user to extract events for
        :type user: User

        :return: A generator of events in ascending chronological order.
        :rtype: generator[Event]
        """

        for ev in cls.objects(user=user, viewed=False):
            yield ev.to_event()

    @classmethod
    def mark_events_as_read(cls, user: User) -> None:
        """
        Mark all user events as viewed

        :param user: The user to mark unseed events as viewed
        :type user: User

        :return: Nothing. None. Empty. Long Gone
        :rtype: None
        """
        cls.objects(user=user, viewed=False).update(set__viewed=True)

    @classmethod
    def get_all_events(cls, user: User) -> Iterator:
        """
        Returns aggregated and sorted generator of events (achievements & level-ups)
        user'd been given

        :param user: The user to extract events for
        :type user: User

        :return: A generator of events in ascending chronological order.
        :rtype: generator[Event]
        """

        for ev in cls.objects(user=user):
            yield ev.to_event()

    @classmethod
    def count_of_tasks_done_by_user(cls, user: User) -> int:
        """
        Number of tasks finished by current user

        :param user: User instance
        :type user: User

        :return: Count of tasks done
        :rtype: int
        """
        return cls.objects(user=user, answer__exists=True).count()

    @classmethod
    def amount_of_money_donated(cls, user: User) -> float:
        """
        Amount of money donatedby current user

        :param user: User instance
        :type user: User

        :return: Amount of money
        :rtype: float
        """

        query = Q(acceptor_fund__ne=None)

        if user is not None:
            query &= Q(user=user)

        return -cls.objects(query).sum('coins')

    @classmethod
    def amount_of_money_earned(cls, user: User) -> float:
        """
        Amount of money earned by current user

        :param user: User instance
        :type user: User

        :return: Amount of money
        :rtype: float
        """

        query = Q(coins__gt=0)

        if user is not None:
            query &= Q(user=user)

        return cls.objects(query).sum('coins')

    @classmethod
    def batches_user_worked_on(cls, user: User) -> Iterator:
        """
        Returns an iterable of deduplicated batches user has worked on before.

        :param user: User instance
        :type user: User

        :return: Iterator over batches
        :rtype: Iterator[Batch]
        """
        seen = set()

        for ev in cls.objects(user=user, answer__exists=True).only('answer'):
            batch = ev.answer.task.batch

            if batch.id not in seen:
                seen.add(batch.id)

                yield batch

    def __str__(self) -> str:
        return 'EventModel({model})'.format(model=str(self.to_event()))

    def __repr__(self) -> str:
        return str(self)
