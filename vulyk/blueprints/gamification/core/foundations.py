# -*- coding: utf-8 -*-
"""
Foundations
"""

from io import IOBase

__all__ = ["Fund"]


class Fund:
    """
    Outer representation of different foundations we should keep:
    donatable or not they are.
    """

    __slots__ = ["description", "donatable", "email", "id", "logo", "name", "site"]

    def __init__(
        self, fund_id: str, name: str, description: str, site: str, email: str, logo: IOBase, *, donatable: bool
    ) -> None:
        """Initialize a Fund.

        :param fund_id: Unique identifier for this fund
        :param name: Display name of the fund
        :param description: Detailed description
        :param site: URL to the fund's website
        :param email: Contact email address
        :param logo: File-like object containing the fund's logo image
        :param donatable: Whether users can donate to this fund
        """
        self.id = fund_id
        self.name = name
        self.description = description
        self.site = site
        self.email = email
        # this one should be an image file or *FSProxy, not sure yet
        self.logo = logo
        self.donatable = donatable

    def to_dict(self) -> dict[str, str | bool]:
        """
        Could be used as a source for JSON or any other representation format.

        :return: Dictionary representation of the fund.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "site": self.site,
            "email": self.email,
            "donatable": self.donatable,
        }

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Fund):
            return other.id == self.id and other.name == self.name
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __str__(self) -> str:
        return "Fund({id}, {name}, {descr}, {site}, {email}, {donat})".format(
            id=self.id,
            name=self.name,
            descr=self.description[:20],
            site=self.site,
            email=self.email,
            donat=self.donatable,
        )

    def __repr__(self) -> str:
        return str(self)
