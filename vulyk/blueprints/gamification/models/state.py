# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import (
    IntField, DateTimeField, ReferenceField, ListField
)

from vulyk.models.user import User

from .rules import RuleModel


class UserStateModel(Document):
    user = ReferenceField(
        document_type=User, db_field='user', required=True)
    level = IntField(min_value=0, default=0)
    points = IntField(min_value=0, default=0)
    actual_coins = IntField(min_value=0, default=0, db_field='actualCoins')
    potential_coins = IntField(
        min_value=0, default=0, db_field='potentialCoins')
    achievements = ListField(
        field=ReferenceField(document_type=RuleModel, required=False))
    last_changed = DateTimeField(db_field='lastChanged')

    meta = {
        'collection': 'gamification.userState',
        'allow_inheritance': True,
        'indexes': [
            'user',
            'last_changed'
        ]
    }
