# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import (
    IntField, DateTimeField, ReferenceField, BooleanField, ListField
)

from vulyk.models.tasks import AbstractAnswer
from vulyk.models.user import User

from .foundations import FundModel
from .rules import RuleModel

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
