# -*- coding: utf-8 -*-
"""
Contains all DB models related to game events.
"""
from flask_mongoengine import Document
from mongoengine import (
    DecimalField, ComplexDateTimeField, ReferenceField, BooleanField, ListField,
    IntField
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
        document_type=AbstractAnswer, db_field='answer', required=False,
        unique=True)
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
                'unique': True
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
            achievements=[a.to_rule() for a in self.achievements],
            acceptor_fund=None
                if self.acceptor_fund is None
                else self.acceptor_fund.to_fund(),
            level_given=self.level_given,
            viewed=self.viewed
        )

    @classmethod
    def from_event(cls, event: Event):
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

    def __str__(self):
        return 'EventModel({model})'.format(model=str(self.to_event()))

    def __repr__(self):
        return str(self)
