# -*- coding: utf-8 -*-
"""
Contains all DB models related to foundations we donate or we rely on
"""
from collections import Iterator
from enum import Enum

from flask_mongoengine import Document
from mongoengine import (
    StringField, EmailField, ImageField, BooleanField, Q
)

from ..core.events import Fund

__all__ = [
    'FundFilterKeys',
    'FundModel'
]


class FundFilterKeys(Enum):
    """
    The intent of this enum is to represent filtering policies.
    """
    NO_FILTER = 0
    DONATABLE = 1
    NON_DONATABLE = 2


class FundModel(Document):
    """
    Database-specific foundation representation
    """
    id = StringField(required=True, max_length=50, primary_key=True)
    name = StringField(required=True)
    description = StringField(required=True)
    site = StringField(required=False)
    email = EmailField(required=False, allow_utf8_user=True)
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
            logo=self.logo.get(),
            donatable=self.donatable)

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
            donatable=fund.donatable)
        result.logo.put(fund.logo)

        return result

    @classmethod
    def find_by_id(cls, fund_id: str) -> Fund:
        """
        Convenience method that returns an optional fund by its ID.

        :param fund_id: Fund's ID
        :type fund_id: str

        :return: Found
        :rtype: Fund|None
        """
        result = None

        try:
            result = FundModel.objects.get(id=fund_id).to_fund()
        except cls.DoesNotExist:
            pass

        return result

    @classmethod
    def get_all(
        cls, filter_by: FundFilterKeys = FundFilterKeys.NO_FILTER
    ) -> Iterator:
        """

        :param filter_by:
        :type filter_by: FundFilterKeys

        :return:
        :rtype: Iterator[Fund]
        """
        criteria = Q()

        if filter_by != FundFilterKeys.NO_FILTER:
            if filter_by == FundFilterKeys.DONATABLE:
                criteria = Q(donatable=True)
            elif filter_by == FundFilterKeys.NON_DONATABLE:
                criteria = Q(donatable=False)

        yield from map(lambda f: f.to_fund(), cls.objects(criteria))

    def __str__(self):
        return 'FundModel({model})'.format(model=str(self.to_fund()))

    def __repr__(self):
        return str(self)
