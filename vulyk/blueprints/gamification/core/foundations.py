# -*- coding: utf-8 -*-
"""
Foundations
"""
from io import IOBase

__all__ = [
    'Fund'
]


class Fund:
    """
    Outer representation of different foundations we should keep:
    donatable or not they are.
    """
    __slots__ = [
        'id',
        'name',
        'description',
        'site',
        'email',
        'logo',
        'donatable'
    ]

    def __init__(self,
                 fund_id: str,
                 name: str,
                 description: str,
                 site: str,
                 email: str,
                 logo: IOBase,
                 donatable: bool) -> None:
        # let's put it manually to use as an alias
        """
        :type fund_id: str
        :type name: str
        :type description: str
        :type site: str
        :type email: str
        :type logo: IOBase
        :type donatable: bool
        """
        self.id = fund_id
        self.name = name
        self.description = description
        self.site = site
        self.email = email
        # this one should be an image file or *FSProxy, not sure yet
        self.logo = logo
        self.donatable = donatable

    def to_dict(self) -> dict:
        """
        Could be used as a source for JSON or any other representation format

        :return: Dict-ized object view
        :rtype: dict
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'site': self.site,
            'email': self.email,
            'donatable': self.donatable
        }

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Fund):
            return o.id == self.id and o.name == self.name
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return 'Fund({id}, {name}, {descr}, {site}, {email}, {donat})'.format(
            id=self.id,
            name=self.name,
            descr=self.description[:20],
            site=self.site,
            email=self.email,
            donat=self.donatable)

    def __repr__(self) -> str:
        return str(self)
