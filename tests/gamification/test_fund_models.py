# -*- coding: utf-8 -*-
"""
test_fund_models
"""
import base64
from tempfile import TemporaryFile

from vulyk.blueprints.gamification.core.foundations import Fund
from vulyk.blueprints.gamification.models.foundations import FundModel

from ..base import BaseTest


class TestEventModels(BaseTest):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

        FundModel.objects.delete()

    def test_fund_ok(self):
        with TemporaryFile('w+b', suffix='.jpg') as f:
            load = b'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAAbElEQVR' \
                   b'4nO3Q0QmAMBAFwWitKSvFWsOKECIz/8c7dgwAAAAAAAAAAAAAADjHtW' \
                   b'15zve3a333R3BvWT2UWIFYgViBWIFYgViBWIFYgViBWIFYgViBWIFYg' \
                   b'ViBWIFYgVgAAAAAAAAAAAAAAPBTD1i3AiiQSFCiAAAAAElFTkSuQmCC'
            logo_bytes = base64.b64decode(load)
            f.write(logo_bytes)

            fund = Fund(
                fund_id='newfund',
                name='New fund',
                description='description',
                site='site.com',
                email='email@email.ek',
                logo=f,
                donatable=True)
            FundModel.from_fund(fund).save()
            fund2 = FundModel.objects.get(id=fund.id).to_fund()

            self.assertEqual(fund, fund2, 'Fund wasn\'t saved and restored')
            self.assertEqual(logo_bytes, fund2.logo.read(),
                             'Fund\'s logo wasn\'t saved and restored')
