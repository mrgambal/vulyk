# -*- coding: utf-8 -*-
"""
The core of gamification sub-project.
"""
from decimal import Decimal

import flask
from flask_login import AnonymousUserMixin

from vulyk import utils
from vulyk.blueprints.gamification.core.foundations import Fund
from vulyk.blueprints.gamification.models.foundations import (
    FundModel, FundFilterBy)
from vulyk.blueprints.gamification import listeners
from vulyk.blueprints.gamification.models.rules import (
    AllRules, ProjectAndFreeRules, RuleModel, StrictProjectRules)
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.services import (
    DonationResult, DonationsService, StatsService)
from vulyk.models.user import User
from vulyk.admin.models import AuthModelView, CKTextAreaField


from .. import VulykModule

__all__ = [
    'gamification'
]


class FundAdmin(AuthModelView):
    form_overrides = dict(description=CKTextAreaField)
    column_exclude_list = ['description', 'logo']


class GamificationModule(VulykModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config['levels'] = {
            k: 1 if k == 1 else (k - 1) * 25 for k in range(1, 51)
        }

    def register(self, app, options, first_registration=False):
        super().register(app, options, first_registration)

        if app.config.get('ENABLE_ADMIN', False):
            app.admin.add_view(FundAdmin(FundModel))
            app.admin.add_view(AuthModelView(RuleModel))

    def get_level(self, points):
        """
        Obtains the level that corresponds to a number of points

        :param points: Number of points
        :type points: Decimal

        :return: Level
        :rtype: int
        """

        for k in sorted(self.config['levels'].keys(), reverse=True):
            if points >= self.config['levels'][k]:
                return k

        return 0


gamification = GamificationModule('gamification', __name__)


@gamification.route('/badges', methods=['GET'])
@gamification.route(
    '/badges/<string:project>/<string:strictness>', methods=['GET'])
def badges(project: str = None, strictness: str = None) -> flask.Response:
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
    :rtype: flask.Response
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
def funds(category: str = None) -> flask.Response:
    """
    The list of foundations we donate to or those, that backed us.
    May be filtered using `category` parameter that currently takes two values
    `donatable` and `nondonatable`. If a full list is needed – parameter must
    be omitted.

    :param category: Filter list
    :type category: str

    :return: Funds list filtered by category (if passed).
    :rtype: flask.Response
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
def fund_logo(fund_id: str) -> flask.Response:
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
    :rtype: flask.Response
    """
    fund = FundModel.find_by_id(fund_id)  # type: Union[Fund, None]

    if fund is None:
        flask.abort(utils.HTTPStatus.NOT_FOUND)

    return flask.send_file(
        fund.logo,
        mimetype='image/{}'.format(fund.logo.format.lower()),
        cache_timeout=360000)


@gamification.route('/events/unseen', methods=['GET'])
def unseen_events() -> flask.Response:
    """
    The list of yet unseen events we return for currently logged in user.

    :return: Events list (may be empty) or Forbidden if not authorized.
    :rtype: flask.Response
    """
    user = flask.g.user  # type: Union[User, AnonymousUserMixin]

    if isinstance(user, User):
        return utils.json_response({
            'events': map(
                lambda e: utils.blacklist(e.to_dict(), ["answer"]),
                EventModel.get_unread_events(user))})
    else:
        flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route('/events/all', methods=['GET'])
def all_events() -> flask.Response:
    """
    The list of all events we return for currently logged in user.

    :return: Events list (may be empty) or Forbidden if not authorized.
    :rtype: flask.Response
    """
    user = flask.g.user  # type: Union[User, AnonymousUserMixin]

    if isinstance(user, User):
        return utils.json_response({
            'events': map(
                lambda e: utils.blacklist(e.to_dict(), ["answer"]),
                EventModel.get_all_events(user))})
    else:
        flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route('/users/me/state', methods=['GET'])
@gamification.route('/users/<string:user_id>/state', methods=['GET'])
def users_state(user_id: str = None) -> flask.Response:
    """
    The collected state of the user within the gamification subsystem.
    Could be created for the very first time asked (if hasn't yet).

    :param user_id: Needed user ID
    :type user_id: str

    :return: An response with a state or 404 if user is not found.
    :rtype: flask.Response
    """

    if user_id is not None:
        user = User.get_by_id(user_id)  # type: Union[User, None]
    else:
        user = flask.g.user  # type: Union[User, AnonymousUserMixin]

    if isinstance(user, User):
        state = UserStateModel.get_or_create_by_user(user)
        return utils.json_response({'state': state.to_dict()})
    else:
        flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route('/donations', methods=['POST'])
def donate() -> flask.Response:
    """
    Performs a money donation to specified fund.

    :return: Usual JSON response
    :rtype: flask.Response
    """
    user = flask.g.user  # type: Union[User, AnonymousUserMixin]

    if isinstance(user, AnonymousUserMixin):
        flask.abort(utils.HTTPStatus.FORBIDDEN)

    fund_id = flask.request.form.get('fund_id')  # type: str
    amount = flask.request.form.get('amount')  # type: int

    try:
        amount = Decimal(amount)
    except ValueError:
        return flask.abort(utils.HTTPStatus.BAD_REQUEST)

    result = DonationsService(user, fund_id, amount).donate()

    if result == DonationResult.SUCCESS:
        return utils.json_response({'done': True})
    elif result == DonationResult.BEGGAR:
        return utils.json_response(
            result={'done': False},
            errors=['Not enough money on your active account'],
            status=utils.HTTPStatus.BAD_REQUEST)
    elif result == DonationResult.STINGY:
        return utils.json_response(
            result={'done': False},
            errors=['Wrong amount passed'],
            status=utils.HTTPStatus.BAD_REQUEST)
    elif result == DonationResult.LIAR:
        return utils.json_response(
            result={'done': False},
            errors=['Wrong fund ID passed'],
            status=utils.HTTPStatus.BAD_REQUEST)
    elif result == DonationResult.ERROR:
        return utils.json_response(
            result={'done': False},
            errors=['Something wrong happened'],
            status=utils.HTTPStatus.BAD_REQUEST)


def get_stats_service():
    return {
        'stats_service': StatsService
    }


gamification.add_context_filler(get_stats_service)
