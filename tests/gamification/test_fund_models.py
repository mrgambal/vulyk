# -*- coding: utf-8 -*-
"""
test_fund_models
"""
import unittest

import flask

from vulyk import utils
from vulyk.blueprints.gamification import gamification
from vulyk.blueprints.gamification.models.foundations import (
    FundModel, FundFilterBy)

from .fixtures import FixtureFund
from ..base import BaseTest


class TestFundModels(BaseTest):
    def tearDown(self):
        super().tearDown()

        FundModel.objects.delete()
        FundModel._get_db()['images.files'].remove()
        FundModel._get_db()['images.chunks'].remove()

    def test_fund_ok(self):
        fund = FixtureFund.get_fund()
        fund2 = FundModel.find_by_id(fund.id)

        self.assertEqual(fund, fund2, 'Fund wasn\'t saved and restored')
        self.assertEqual(FixtureFund.LOGO_BYTES, fund2.logo.read(),
                         'Fund\'s logo wasn\'t saved and restored')

    def test_logo_controller(self):
        app = flask.Flask('test')
        app.config.from_object('vulyk.settings')
        app.register_blueprint(gamification, url_prefix='/gamification')

        fund = FixtureFund.get_fund()

        resp = app.test_client().get('/gamification/funds/{id}/logo'
                                     .format(id=fund.id))
        self.assertEqual(resp.mimetype, 'image/png')
        self.assertEqual(resp.status_code, utils.HTTPStatus.OK)
        self.assertEqual(resp.data, FixtureFund.LOGO_BYTES)

    def test_fund_to_dict(self):
        fund = FixtureFund.get_fund()
        expected = {
            'id': FixtureFund.FUND_ID,
            'name': FixtureFund.FUND_NAME,
            'description': FixtureFund.FUND_DESCRIPTION,
            'site': FixtureFund.FUND_SITE,
            'email': FixtureFund.FUND_EMAIL,
            'donatable': True}

        self.assertDictEqual(expected, fund.to_dict())

    def test_get_all_funds(self):
        FixtureFund.get_fund('fund1', 'Fund 1'),
        FixtureFund.get_fund('fund2', 'Fund 2', False)

        self.assertEqual(
            len(list(FundModel.get_funds())), 2,
            'Not all funds were fetched')

    def test_get_donatable_funds(self):
        FixtureFund.get_fund('fund1', 'Fund 1'),
        FixtureFund.get_fund('fund2', 'Fund 2', False)
        result = list(FundModel.get_funds(FundFilterBy.DONATABLE))

        self.assertEqual(len(result), 1, 'A single fund must be fetched')
        self.assertEqual(result[0].name, 'Fund 1')

    def test_get_non_donatable_funds(self):
        FixtureFund.get_fund('fund1', 'Fund 1'),
        FixtureFund.get_fund('fund2', 'Fund 2', False)
        result = list(FundModel.get_funds(FundFilterBy.NON_DONATABLE))

        self.assertEqual(len(result), 1, 'A single fund must be fetched')
        self.assertEqual(result[0].name, 'Fund 2')


if __name__ == '__main__':
    unittest.main()
