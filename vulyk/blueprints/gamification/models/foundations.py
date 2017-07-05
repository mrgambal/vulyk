# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import (
    StringField, EmailField, ImageField, BooleanField
)

__all__ = [
    'FundModel'
]


class FundModel(Document):
    """
    Database-specific foundation representation
    """
    name = StringField(required=True)
    description = StringField(required=True)
    site = StringField(required=False)
    email = EmailField(required=False, allow_utf8_user=True)
    # not sure how that mess works. Also a special type of controller needed
    logo = ImageField()
    donateable = BooleanField(required=True)

    meta = {
        'collection': 'gamification.funds',
        'allow_inheritance': True,
        'indexes': [
            'name',
            'donateable'
        ]
    }
