# -*- coding: utf-8 -*-
"""
The core of gamification sub-project.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, ClassVar

import flask
import wtforms
from flask_login import AnonymousUserMixin

from vulyk import utils
from vulyk.admin.models import AuthModelView, CKTextAreaField, RequiredBooleanField
from vulyk.blueprints.gamification.models.events import EventModel
from vulyk.blueprints.gamification.models.foundations import Fund, FundFilterBy, FundModel
from vulyk.blueprints.gamification.models.rules import AllRules, ProjectAndFreeRules, RuleModel, StrictProjectRules
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.blueprints.gamification.services import DonationResult, DonationsService, StatsService
from vulyk.models.user import User

from .. import VulykModule

__all__ = ["gamification"]


class FundAdmin(AuthModelView):
    form_overrides: ClassVar[dict[str, Any]] = {
        "description": CKTextAreaField,
        "donatable": RequiredBooleanField,
    }

    column_exclude_list: ClassVar[list[str]] = ["description", "logo"]


class RuleAdmin(AuthModelView):
    form_overrides: ClassVar[dict[str, Any]] = {"description": CKTextAreaField}

    column_exclude_list: ClassVar[list[str]] = ["description"]


class GamificationModule(VulykModule):
    def __init__(self, *args: Sequence[Any], **kwargs: Mapping[str, Any]) -> None:
        super().__init__(*args, **kwargs)

        self.config["levels"] = {k: 1 if k == 1 else (k - 1) * 25 for k in range(1, 51)}

    def register(self, app: flask.Flask, options: dict[str, Any]) -> None:
        super().register(app, options)

        if app.config.get("ENABLE_ADMIN", False):
            app.admin.add_view(FundAdmin(FundModel))

            if self.config.get("badges"):
                if not getattr(RuleAdmin, "form_overrides"):  # noqa: B009
                    RuleAdmin.form_overrides = {}

                RuleAdmin.form_overrides["badge"] = wtforms.fields.SelectField

                if not getattr(RuleAdmin, "form_args"):  # noqa: B009
                    RuleAdmin.form_args = {}

                RuleAdmin.form_args["badge"] = {"label": "Pick badge image", "choices": self.config["badges"]}

            app.admin.add_view(RuleAdmin(RuleModel))

    def get_level(self, points: Decimal) -> int:
        """
        Obtains the level that corresponds to a number of points.

        :param points: Number of points.

        :return: Level.
        """

        for k in sorted(self.config["levels"].keys(), reverse=True):
            if points >= self.config["levels"][k]:
                return k

        return 0


gamification = GamificationModule("gamification", __name__)


@gamification.route("/badges", methods=["GET"])
@gamification.route("/badges/<string:project>/<string:strictness>", methods=["GET"])
def badges(project: str | None = None, strictness: str | None = None) -> flask.Response:
    """
    Prepares a list of badges with either no filters or different filtering
    policies within a task type (project).
    When no project specified - all badges will return.
    In case if project is passed there is two possible options to filter them:

    > 'weak' - rules related to the project + rules with no project;
    > 'strict' - rules related to the project ONLY.

    :param project: Task type name
    :param strictness: Filtering policy: 'strict' or 'weak'

    :return: List of badges (rules).
    """
    filtering: AllRules = AllRules()

    if project is not None:
        if strictness == "strict":
            filtering = StrictProjectRules(project)  # type: ignore[override]
        elif strictness == "weak":
            filtering = ProjectAndFreeRules(project)  # type: ignore[override]
        else:
            flask.abort(utils.HTTPStatus.NOT_FOUND)

    return utils.json_response(
        {"badges": (r.to_dict() for r in RuleModel.get_actual_rules([], filtering, is_weekend=True))}
    )


@gamification.route("/funds", methods=["GET"])
@gamification.route("/funds/<string:category>", methods=["GET"])
def funds(category: str | None = None) -> flask.Response:
    """
    The list of foundations we donate to or those, that backed us.
    May be filtered using `category` parameter that currently takes two values
    `donatable` and `nondonatable`. If a full list is needed - parameter must
    be omitted.

    :param category: Filter list.

    :return: Funds list filtered by category (if passed).
    """
    filtering = FundFilterBy.NO_FILTER

    if category is not None:
        if category == "donatable":
            filtering = FundFilterBy.DONATABLE
        elif category == "nondonatable":
            filtering = FundFilterBy.NON_DONATABLE
        else:
            flask.abort(utils.HTTPStatus.NOT_FOUND)

    return utils.json_response({"funds": (f.to_dict() for f in FundModel.get_funds(filtering))})


@gamification.route("/funds/<string:fund_id>/logo", methods=["GET"])
def fund_logo(fund_id: str) -> flask.Response:
    """
    Simple controller that will return you a logotype of the fund if it exists
    in the DB by fund's ID.
    To fulfill mimetype we use that fact that ImageGridFSProxy relies on
    Pillow's Image class that recognises correct mimetype for images. Thus the
    proxy has a field named `format`, which contain an uppercase name of
    the type. E.g.: 'JPEG'.

    :param fund_id: Current fund ID.

    :return: An response with a file or 404 if fund is not found.
    """
    fund: Fund | None = FundModel.find_by_id(fund_id)

    if fund is None or fund.logo is None:
        flask.abort(utils.HTTPStatus.NOT_FOUND)

    return flask.send_file(fund.logo, mimetype="image/{}".format(fund.logo.format.lower()))


@gamification.route("/events/unseen", methods=["GET"])  # noqa: RET503
def unseen_events() -> flask.Response:
    """
    The list of yet unseen events we return for currently logged in user.

    :return: Events list (may be empty) or Forbidden if not authorized.
    """
    user: User | AnonymousUserMixin = flask.g.user

    if isinstance(user, User):
        return utils.json_response(
            {"events": (e.to_dict(ignore_answer=True) for e in EventModel.get_unread_events(user))}
        )

    flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route("/events/mark_viewed", methods=["GET"])  # noqa: RET503
def mark_viewed() -> flask.Response:
    """
    Mark all events as viewed for currently logged in user.

    :return: Successful response or Forbidden if not authorized.
    """
    user: User | AnonymousUserMixin = flask.g.user

    if isinstance(user, User):
        EventModel.mark_events_as_read(user)
        return utils.json_response({})

    flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route("/events/all", methods=["GET"])  # noqa: RET503
def all_events() -> flask.Response:
    """
    The list of all events we return for currently logged in user.

    :return: Events list (may be empty) or Forbidden if not authorized.
    """
    user: User | AnonymousUserMixin = flask.g.user

    if isinstance(user, User):
        return utils.json_response({"events": (e.to_dict(ignore_answer=True) for e in EventModel.get_all_events(user))})

    flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route("/users/me/state", methods=["GET"])  # noqa: RET503
@gamification.route("/users/<string:user_id>/state", methods=["GET"])
def users_state(user_id: str | None = None) -> flask.Response:
    """
    The collected state of the user within the gamification subsystem.
    Could be created for the very first time asked (if hasn't yet).

    :param user_id: Needed user ID

    :return: An response with a state or 404 if user is not found.
    """
    user: User | AnonymousUserMixin | None

    user = User.get_by_id(user_id) if user_id is not None else flask.g.user  # type: ignore[assignment]

    if isinstance(user, User):
        state = UserStateModel.get_or_create_by_user(user)
        return utils.json_response({"state": state.to_dict()})

    flask.abort(utils.HTTPStatus.FORBIDDEN)


@gamification.route("/donations", methods=["POST"])
def donate() -> flask.Response:
    """
    Performs a money donation to specified fund.

    :return: Usual JSON response
    """
    user: User | AnonymousUserMixin = flask.g.user

    if isinstance(user, AnonymousUserMixin):
        flask.abort(utils.HTTPStatus.FORBIDDEN)

    fund_id: str = str(flask.request.form.get("fund_id"))
    amount: int = int(flask.request.form.get("amount"))

    try:
        amount_decimal = Decimal(amount)
    except ValueError:
        flask.abort(utils.HTTPStatus.BAD_REQUEST)

    result = DonationsService(user, fund_id, amount_decimal).donate()

    if result == DonationResult.SUCCESS:
        return utils.json_response({"done": True})
    if result == DonationResult.BEGGAR:
        return utils.json_response(
            result={"done": False},
            errors=["Not enough money on your active account"],
            status=utils.HTTPStatus.BAD_REQUEST,
        )
    if result == DonationResult.STINGY:
        return utils.json_response(
            result={"done": False}, errors=["Wrong amount passed"], status=utils.HTTPStatus.BAD_REQUEST
        )
    if result == DonationResult.LIAR:
        return utils.json_response(
            result={"done": False}, errors=["Wrong fund ID passed"], status=utils.HTTPStatus.BAD_REQUEST
        )

    return utils.json_response(
        result={"done": False}, errors=["Something wrong happened"], status=utils.HTTPStatus.BAD_REQUEST
    )


def get_stats_service() -> dict[str, type[StatsService]]:
    return {"stats_service": StatsService}


gamification.add_context_filler(get_stats_service)
