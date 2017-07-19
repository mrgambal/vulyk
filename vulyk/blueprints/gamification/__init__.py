# -*- coding: utf-8 -*-
"""
The core of gamification sub-project.
"""
import flask
from flask import Blueprint, Response, send_file

from vulyk import utils
from vulyk.blueprints.gamification.models.foundations import (
    FundModel, FundFilterBy)
from vulyk.blueprints.gamification.models.rules import (
    AllRules, ProjectAndFreeRules, RuleModel, StrictProjectRules)
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.models.user import User

from . import listeners
from .models.events import EventModel

__all__ = [
    'gamification'
]

gamification = Blueprint('gamification', __name__)


@gamification.route('/badges', methods=['GET'])
@gamification.route(
    '/badges/<string:project>/<string:strictness>', methods=['GET'])
def badges(project: str = None, strictness: str = None) -> Response:
    """
    Prepares a list of badges with either no filters or different filtering
    policies within a task type (project).
    When no project specified – all badges will return.
    In case if project is passed there is two possible options to filter them:

    > 'weak' – rules related to the project + rules with no project;
    > 'strict' – rules related to the project ONLY.

    :param project: Task type name
    :type project: str
    :param strictness: Filtering policy: 'strict' or 'weak'
    :type strictness: str

    :return: List of badges (rules).
    :rtype: Response
    """
    filtering = AllRules()

    if project is not None:
        if strictness == 'strict':
            filtering = StrictProjectRules(project)
        elif strictness == 'weak':
            filtering = ProjectAndFreeRules(project)
        else:
            flask.abort(utils.HTTPStatus.NOT_FOUND)

    return utils.json_response(
        {'badges': map(
            lambda r: r.to_dict(),
            RuleModel.get_actual_rules([], filtering, True))})


@gamification.route('/funds', methods=['GET'])
@gamification.route('/funds/<string:category>', methods=['GET'])
def funds(category: str = None) -> Response:
    """
    The list of foundations we donate to or those, that backed us.
    May be filtered using `category` parameter that currently takes two values
    `donatable` and `nondonatable`. If a full list is needed – parameter must
    be omitted.

    :param category: Filter list
    :type category: str

    :return: Funds list filtered by category (if passed).
    :rtype: Response
    """
    filtering = FundFilterBy.NO_FILTER

    if category is not None:
        if category == 'donatable':
            filtering = FundFilterBy.DONATABLE
        elif category == 'nondonatable':
            filtering = FundFilterBy.NON_DONATABLE
        else:
            flask.abort(utils.HTTPStatus.NOT_FOUND)

    return utils.json_response(
        {'funds': map(
            lambda f: f.to_dict(),
            FundModel.get_funds(filtering))})


@gamification.route('/funds/<string:fund_id>/logo', methods=['GET'])
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


@gamification.route('/events', methods=['GET'])
def unseen_events() -> Response:
    """
    The list of yet unseen events we return for currently logged in user.

    :return: Events list (may be empty) or Forbidden if not authorized.
    :rtype: Response
    """
    user = flask.g.user

    if isinstance(user, User):
        return utils.json_response({
            'events': map(
                lambda e: e.to_dict(),
                EventModel.get_unread_events(flask.g.user))})
    else:
        flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route('/users/<string:user_id>/state', methods=['GET'])
def users_state(user_id: str) -> Response:
    """
    The collected state of the user within the gamification subsystem.
    Could be created for the very first time asked (if hasn't yet).

    :param user_id: Needed user ID
    :type user_id: str

    :return: An response with a state or 404 if user is not found.
    :rtype: Response
    """
    user = User.get_by_id(user_id)

    if isinstance(user, User):
        state = UserStateModel.get_or_create_by_user(user)
        return utils.json_response({'state': state.to_dict()})
    else:
        flask.abort(utils.HTTPStatus.FORBIDDEN)
