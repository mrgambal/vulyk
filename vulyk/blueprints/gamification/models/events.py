# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import (
    IntField, DateTimeField, ReferenceField, BooleanField, ListField
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
    timestamp = DateTimeField(required=True)
    user = ReferenceField(
        document_type=User, db_field='user', required=True)
    answer = ReferenceField(
        document_type=AbstractAnswer, db_field='answer', required=False,
        unique=True)
    # points must only be added
    points_given = IntField(min_value=0, required=True, db_field='points')
    # coins can be both given and withdrawn
    coins = IntField(required=True)
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
            acceptor_fund_id=self.acceptor_fund,
            level_given=self.level_given,
            viewed=self.viewed
        )

    @classmethod
    def from_event(cls, event: Event):
        """
        Event to DB-specific model converter.

        :param event: Source event instance
        :type event: Event

        :return: Full-bodied model
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
            acceptor_fund_id=event.acceptor_fund_id,
            level_given=event.level_given,
            viewed=event.viewed
        )

    def __str__(self):
        return 'EventModel({model})'.format(model=str(self.to_event()))

    def __repr__(self):
        return str(self)
