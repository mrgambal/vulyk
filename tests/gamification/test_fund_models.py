# -*- coding: utf-8 -*-
"""
test_fund_models
"""

import unittest
from io import BytesIO

import flask
from PIL import Image, ImageChops

from vulyk import utils
from vulyk.blueprints.gamification import gamification
from vulyk.blueprints.gamification.models.foundations import FundFilterBy, FundModel

from ..base import BaseTest
from .fixtures import FixtureFund


class TestFundModels(BaseTest):
    def tearDown(self) -> None:
        super().tearDown()

        FundModel.objects.delete()
        FundModel._get_db()["images.files"].drop()
        FundModel._get_db()["images.chunks"].drop()

    def test_fund_ok(self) -> None:
        fund = FixtureFund.get_fund()
        fund2 = FundModel.find_by_id(fund.id)

        self.assertEqual(fund, fund2, "Fund wasn't saved and restored")
        # ImageField generates thumbnails / re-encodes images during save; compare
        # decoded pixel content instead of raw compressed bytes to be platform-agnostic
        a = Image.open(BytesIO(FixtureFund.LOGO_BYTES)).convert("RGBA")
        b = Image.open(BytesIO(fund2.logo.read())).convert("RGBA")
        self.assertEqual(a.size, b.size)
        self.assertIsNone(ImageChops.difference(a, b).getbbox(), "Fund's logo wasn't saved and restored")

    def test_logo_controller(self) -> None:
        app = flask.Flask("test")
        app.config.from_object("vulyk.settings")
        app.register_blueprint(gamification, url_prefix="/gamification")

        fund = FixtureFund.get_fund()

        resp = app.test_client().get("/gamification/funds/{id}/logo".format(id=fund.id))
        self.assertEqual(resp.mimetype, "image/png")
        self.assertEqual(resp.status_code, utils.HTTPStatus.OK)
        a = Image.open(BytesIO(FixtureFund.LOGO_BYTES)).convert("RGBA")
        b = Image.open(BytesIO(resp.data)).convert("RGBA")
        self.assertEqual(a.size, b.size)
        self.assertIsNone(ImageChops.difference(a, b).getbbox(), "Returned logo doesn't match expected image")

    def test_fund_to_dict(self) -> None:
        fund = FixtureFund.get_fund()
        expected = {
            "id": FixtureFund.FUND_ID,
            "name": FixtureFund.FUND_NAME,
            "description": FixtureFund.FUND_DESCRIPTION,
            "site": FixtureFund.FUND_SITE,
            "email": FixtureFund.FUND_EMAIL,
            "donatable": True,
        }

        self.assertDictEqual(expected, fund.to_dict())

    def test_get_all_funds(self) -> None:
        FixtureFund.get_fund("fund1", "Fund 1")
        FixtureFund.get_fund("fund2", "Fund 2", donatable=False)

        self.assertEqual(len(list(FundModel.get_funds())), 2, "Not all funds were fetched")

    def test_get_donatable_funds(self) -> None:
        FixtureFund.get_fund("fund1", "Fund 1")
        FixtureFund.get_fund("fund2", "Fund 2", donatable=False)
        result = list(FundModel.get_funds(FundFilterBy.DONATABLE))

        self.assertEqual(len(result), 1, "A single fund must be fetched")
        self.assertEqual(result[0].name, "Fund 1")

    def test_get_non_donatable_funds(self) -> None:
        FixtureFund.get_fund("fund1", "Fund 1")
        FixtureFund.get_fund("fund2", "Fund 2", donatable=False)
        result = list(FundModel.get_funds(FundFilterBy.NON_DONATABLE))

        self.assertEqual(len(result), 1, "A single fund must be fetched")
        self.assertEqual(result[0].name, "Fund 2")


if __name__ == "__main__":
    unittest.main()
