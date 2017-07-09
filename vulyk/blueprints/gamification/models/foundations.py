# -*- coding: utf-8 -*-
"""
Contains all DB models related to foundations we donate or we rely on
"""
from flask_mongoengine import Document
from mongoengine import (
    StringField, EmailField, ImageField, BooleanField
)

from ..core.events import Fund

__all__ = [
    'FundModel'
]


class FundModel(Document):
    """
    Database-specific foundation representation
    """
    id = StringField(required=True, max_length=50, primary_key=True)
    name = StringField(required=True)
    description = StringField(required=True)
    site = StringField(required=False)
    email = EmailField(required=False, allow_utf8_user=True)
    # not sure how that mess works. Also a special type of controller needed
    logo = ImageField(unique=True)
    donatable = BooleanField(required=True)

    meta = {
        'collection': 'gamification.funds',
        'allow_inheritance': True,
        'indexes': [
            'name',
            'donatable'
        ]
    }

    def to_fund(self) -> Fund:
        """
        DB-specific model to Fund converter.

        :return: New Fund instance
        :rtype: Fund
        """
        return Fund(
            fund_id=self.id,
            name=self.name,
            description=self.description,
            site=self.site,
            email=self.email,
            logo=self.logo.read(),
            donatable=self.donatable
        )

    @classmethod
    def from_fund(cls, fund: Fund):
        """
        Fund to DB-specific model converter.

        :param fund: Current Fund instance
        :type fund: Fund

        :return: New FundModel instance
        :rtype: FundModel
        """
        result = cls(
            id=fund.id,
            name=fund.name,
            description=fund.description,
            site=fund.site,
            email=fund.email,
            donatable=fund.donatable
        )
        result.logo.put(fund.logo)

        return result

    def __str__(self):
        return 'FundModel({model})'.format(model=str(self.to_fund()))

    def __repr__(self):
        return str(self)
