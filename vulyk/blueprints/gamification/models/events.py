# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import (
    IntField, DateTimeField, ReferenceField, BooleanField
)

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
    user_id = ReferenceField(document_type=User, db_field='userId',
                             required=True)
    # points must only be added
    points_given = IntField(min_value=0, required=True, db_field='points')
    # coins can be both given and withdrawn
    coins = IntField(required=True)
    achievement = ReferenceField(document_type=RuleModel, required=False)
    acceptor_fund = ReferenceField(document_type=FundModel, required=False,
                                   db_field='acceptorFund')
    level_given = IntField(min_value=1, required=False, db_field='level')
    viewed = BooleanField(default=False, required=True)

    meta = {
        'collection': 'gamification.events',
        'allow_inheritance': True,
        'indexes': [
            'user_id',
            'acceptor_fund',
            'timestamp'
        ]
    }
