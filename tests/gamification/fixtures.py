# -*- coding: utf-8 -*-
import base64
from tempfile import TemporaryFile

from vulyk.blueprints.gamification.core.foundations import Fund
from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk.blueprints.gamification.models.task_types import AbstractGamifiedTaskType

from ..fixtures import FakeAnswer, FakeModel

__all__ = ["FakeType", "FixtureFund"]


class FakeType(AbstractGamifiedTaskType):
    task_model = FakeModel
    answer_model = FakeAnswer
    type_name = "FakeGamifiedTaskType"
    template = "tmpl.html"

    _name = "Fake name"
    _description = "Fake description"


class FixtureFund:
    FUND_ID = "newfund"
    FUND_NAME = "New fund"
    FUND_DESCRIPTION = "description"
    FUND_SITE = "site.com"
    FUND_EMAIL = "email@email.ek"
    FUND_DONATABLE = True
    LOAD = (
        "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAbElEQVR"
        "4nO3Q0QmAMBAFwWitKSvFWsOKECIz/8c7dgwAAAAAAAAAAAAAADjHtW"
        "15zve3a333R3BvWT2UWIFYgViBWIFYgViBWIFYgViBWIFYgViBWIFYg"
        "ViBWIFYgVgAAAAAAAAAAAAAAPBTD1i3AiiQSFCiAAAAAElFTkSuQmCC"
    )
    LOGO_BYTES = base64.b64decode(LOAD)

    @classmethod
    def get_fund(cls, fund_id: str = FUND_ID, name: str = FUND_NAME, *, donatable: bool = FUND_DONATABLE) -> Fund:
        """
        :param name: Fund name.
        :param fund_id: Fund ID.
        :param donatable: Is donatable.

        :return: Fully fledged fund instance.
        """
        with TemporaryFile("w+b", suffix=".jpg") as f:
            f.write(cls.LOGO_BYTES)

            fund = Fund(
                fund_id=fund_id,
                name=name,
                description=cls.FUND_DESCRIPTION,
                site=cls.FUND_SITE,
                email=cls.FUND_EMAIL,
                logo=f,
                donatable=donatable,
            )
            FundModel.from_fund(fund).save()

            return fund
