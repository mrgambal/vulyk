# -*- coding: utf-8 -*-
"""
Contains all DB models related to foundations we donate or we rely on
"""
from enum import Enum
from typing import Iterator, Optional

from flask_mongoengine import Document
from mongoengine import BooleanField, EmailField, ImageField, Q, StringField

from ..core.foundations import Fund

__all__ = [
    'FundFilterBy',
    'FundModel'
]


class FundFilterBy(Enum):
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
    logo = ImageField(unique=True, thumbnail_size=(141, 106, True))
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
    def find_by_id(cls, fund_id: str) -> Optional[Fund]:
        """
        Convenience method that returns an optional fund by its ID.

        :param fund_id: Fund's ID
        :type fund_id: str

        :return: Found instance or none.
        :rtype: Optional[Fund]
        """
        result = None

        try:
            result = FundModel.objects.get(id=fund_id).to_fund()
        except cls.DoesNotExist:
            pass

        return result

    @classmethod
    def get_funds(
        cls,
        filter_by: FundFilterBy = FundFilterBy.NO_FILTER
    ) -> Iterator[Fund]:
        """
        Returns an enumeration of funds available using the filtering policy
        passed.

        :param filter_by: Filtering policy
        :type filter_by: FundFilterBy

        :return: Lazy enumeration of funds available.
        :rtype: Iterator[Fund]
        """
        criteria = Q()

        if filter_by != FundFilterBy.NO_FILTER:
            if filter_by == FundFilterBy.DONATABLE:
                criteria = Q(donatable=True)
            elif filter_by == FundFilterBy.NON_DONATABLE:
                criteria = Q(donatable=False)

        yield from map(lambda f: f.to_fund(), cls.objects(criteria))

    def __str__(self) -> str:
        return 'FundModel({model})'.format(model=str(self.to_fund()))

    def __repr__(self) -> str:
        return str(self)
