# -*- coding: utf-8 -*-
"""
test_fund_models
"""
import base64
from tempfile import TemporaryFile

import flask

from vulyk import utils
from vulyk.blueprints.gamification import gamification
from vulyk.blueprints.gamification.core.foundations import Fund
from vulyk.blueprints.gamification.models.foundations import FundModel

from ..base import BaseTest


class TestFundModels(BaseTest):
    FUND_ID = 'newfund'
    FUND_NAME = 'New fund'
    FUND_DESCRIPTION = 'description'
    FUND_SITE = 'site.com'
    FUND_EMAIL = 'email@email.ek'

    LOAD = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAbElEQVR' \
           b'4nO3Q0QmAMBAFwWitKSvFWsOKECIz/8c7dgwAAAAAAAAAAAAAADjHtW' \
           b'15zve3a333R3BvWT2UWIFYgViBWIFYgViBWIFYgViBWIFYgViBWIFYg' \
           b'ViBWIFYgVgAAAAAAAAAAAAAAPBTD1i3AiiQSFCiAAAAAElFTkSuQmCC'
    LOGO_BYTES = base64.b64decode(LOAD)

    def tearDown(self):
        super().tearDown()

        FundModel.objects.delete()
        FundModel._get_db().drop_collection('images.files')
        FundModel._get_db().drop_collection('images.chunks')

    def test_fund_ok(self):
        fund = self.get_fund()
        fund2 = FundModel.find_by_id(fund.id)

        self.assertEqual(fund, fund2, 'Fund wasn\'t saved and restored')
        self.assertEqual(self.LOGO_BYTES, fund2.logo.read(),
                         'Fund\'s logo wasn\'t saved and restored')

    def test_logo_controller(self):
        app = flask.Flask('test')
        app.config.from_object('vulyk.settings')
        app.register_blueprint(gamification, url_prefix='/gamification')

        fund = self.get_fund()

        resp = app.test_client().get('/gamification/fund/{id}/logo'
                                     .format(id=fund.id))
        self.assertEqual(resp.mimetype, 'image/png')
        self.assertEqual(resp.status_code, utils.HTTPStatus.OK)
        self.assertEqual(resp.data, self.LOGO_BYTES)

    def test_fund_to_dict(self):
        fund = self.get_fund()
        expected = {
            'id': self.FUND_ID,
            'name': self.FUND_NAME,
            'description': self.FUND_DESCRIPTION,
            'site': self.FUND_SITE,
            'email': self.FUND_EMAIL,
            'donatable': True
        }

        self.assertDictEqual(expected, fund.to_dict())

    def get_fund(self) -> Fund:
        with TemporaryFile('w+b', suffix='.jpg') as f:
            f.write(self.LOGO_BYTES)

            fund = Fund(
                fund_id=self.FUND_ID,
                name=self.FUND_NAME,
                description=self.FUND_DESCRIPTION,
                site=self.FUND_SITE,
                email=self.FUND_EMAIL,
                logo=f,
                donatable=True)
            FundModel.from_fund(fund).save()

            return fund
