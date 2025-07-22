# -*- coding: utf-8 -*-
"""
Contains custom fields that extends mongoengine's fields.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from mongoengine.fields import ComplexDateTimeField

__all__ = ["UTCComplexDateTimeField"]


class UTCComplexDateTimeField(ComplexDateTimeField):
    """
    A timezone-aware ComplexDateTimeField that ensures all datetime objects
    are returned with UTC timezone.

    ComplexDateTimeField handles microseconds exactly instead of rounding
    like DateTimeField does, while UTCComplexDateTimeField additionally ensures
    all datetime objects are timezone-aware with UTC timezone.

    The stored string has the following format:
        YYYY,MM,DD,HH,MM,SS,NNNNNN,Z

    Where NNNNNN is the number of microseconds of the represented `datetime`.
    The `,` as the separator can be easily modified by passing the `separator`
    keyword when initializing the field.
    """

    def __init__(self, separator: str = ",", **kwargs: dict[str, Any]) -> None:
        super().__init__(separator, **kwargs)

        if self.separator.isalnum():
            raise ValueError("Separator must not be alphanumeric.")

        self.format = self.separator.join(["%Y", "%m", "%d", "%H", "%M", "%S", "%f", "%Z"])

    def _convert_from_string(self, data: str) -> datetime:
        """
        Convert a string representation to a `datetime` object (the object you
        will manipulate). This is the reverse function of
        `_convert_from_datetime`.

        >>> a = '2011,06,08,20,26,24,092284'
        >>> UTCComplexDateTimeField()._convert_from_string(a)
        datetime.datetime(2011, 6, 8, 20, 26, 24, 92284, tzinfo=ZoneInfo('UTC'))
        """
        raw = data.split(self.separator)
        tzinfo = ZoneInfo(raw.pop()) if len(raw) == 8 else ZoneInfo("UTC")
        year, month, day, hour, minute, second, microsecond = map(int, raw)
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
