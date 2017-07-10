# -*- coding: utf-8 -*-
"""
The core of gamification sub-project.
"""
import flask
from flask import Blueprint, Response, send_file

from vulyk.blueprints.gamification.models.foundations import FundModel
from vulyk import utils

gamification = Blueprint('gamification', __name__)


@gamification.route('/fund/<string:fund_id>/logo')
def fund_logo(fund_id: str) -> Response:
    """
    Simple controller that will return you a logotype of the fund if it exists
    in the DB by fund's ID.
    To fulfill mimetype we use that fact that ImageGridFSProxy relies on
    Pillow's Image class that recognises correct mimetype for images. Thus the
    proxy has a field named `format`, which contain an uppercase name of
    the type. E.g.: 'JPEG'.

    :param fund_id: Current fund ID
    :type fund_id: str

    :return: An response with a file or 404 if fund is not found
    :rtype: Response
    """
    fund = FundModel.find_by_id(fund_id)

    if fund is None:
        flask.abort(utils.HTTPStatus.NOT_FOUND)

    return send_file(fund.logo,
                     mimetype='image/{}'.format(fund.logo.format.lower()),
                     cache_timeout=360000)
