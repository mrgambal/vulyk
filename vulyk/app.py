# -*- coding: utf-8 -*-
"""Die Hauptstadt of our little project. Just a usual Flask application."""
from typing import Dict

import flask
import flask_login as login
from flask import Response

try:
    import ujson as json
except ImportError:
    import json

from vulyk import cli, bootstrap, utils
from vulyk.models.exc import TaskNotFoundError
from vulyk.utils import NO_TASKS

__all__ = [
    'app',
    'TASKS_TYPES'
]

app = bootstrap.init_app(__name__)
TASKS_TYPES = bootstrap.init_plugins(app)


# region Views
@app.route('/', methods=['GET'])
def index() -> Response:
    """
    Main site view.

    :returns: Prepared response.
    :rtype: Response
    """
    task_types = []
    user = flask.g.user

    if user.is_authenticated:
        task_types = [x.to_dict() for x in TASKS_TYPES.values()
                      if user.is_eligible_for(x.type_name)]

    if len(task_types) == 1 and app.config["REDIRECT_USER_AFTER_LOGIN"]:
        return flask.redirect(
            flask.url_for('task_home', type_name=task_types[0]['type']))

    return flask.render_template(utils.get_template_path(app, 'index.html'),
                                 task_types=task_types)


@app.route('/logout', methods=['POST'])
def logout() -> Response:
    """
    An action-view, signs the user out and redirects to the homepage.

    :returns: Prepared response.
    :rtype: Response
    """
    login.logout_user()

    return flask.redirect(flask.url_for('index'))


@app.route('/type/<string:type_name>/next', methods=['GET'])
@login.login_required
def next_page(type_name: str) -> Response:
    """
    Provides next available task for user.
    If user isn't eligible for that type of tasks - an exception
    should be thrown.

    :param type_name: Task type name
    :type type_name: str

    :returns: Prepared response.
    :rtype: Response
    """
    user = flask.g.user
    task_type = utils.resolve_task_type(type_name, TASKS_TYPES, user)

    if task_type is None:
        return NO_TASKS

    task = task_type.get_next(user)

    if not task:
        return NO_TASKS

    return utils.json_response(
        {
            'task': task,
            'stats': user.get_stats(task_type=task_type)
        },
        # doubtful that we need it.
        task_type.template
    )


@app.route('/type/<string:type_name>/', methods=['GET'])
@login.login_required
def task_home(type_name: str) -> Response:
    """
    :param type_name: Task type name
    :type type_name: str

    :returns: Prepared response.
    :rtype: Response
    """
    task_type = utils.resolve_task_type(type_name, TASKS_TYPES, flask.g.user)

    if task_type is None:
        flask.abort(utils.HTTPStatus.NOT_FOUND)

    return flask.render_template(utils.get_template_path(app, 'task.html'),
                                 task_type=task_type)


@app.route('/type/<string:type_name>/leaders', methods=['GET'])
@login.login_required
def leaders(type_name: str) -> Response:
    """
    Display a list of most effective participants.

    :param type_name: Task type name
    :type type_name: str

    :returns: Prepared response.
    :rtype: Response
    """
    task_type = utils.resolve_task_type(type_name, TASKS_TYPES, flask.g.user)

    if task_type is None:
        flask.abort(utils.HTTPStatus.NOT_FOUND)

    return flask.render_template(
        utils.get_template_path(app, 'leaderboard.html'),
        task_type=task_type,
        leaders=task_type.get_leaderboard())


@app.route('/type/<string:type_name>/skip/<string:task_id>', methods=['POST'])
@login.login_required
def skip(type_name: str, task_id: str) -> Response:
    """
    This action adds the task to the 'skipped' list of current user.

    :param type_name: Task type name
    :type type_name: str
    :param task_id: Task ID
    :type task_id: str

    :returns: Prepared response.
    :rtype: Response
    """
    user = flask.g.user
    task_type = utils.resolve_task_type(type_name, TASKS_TYPES, user)

    if task_type is None:
        return NO_TASKS

    try:
        task_type.skip_task(user=user, task_id=task_id)
    except TaskNotFoundError:
        return NO_TASKS

    return utils.json_response({'done': True})


@app.route('/type/<string:type_name>/done/<string:task_id>', methods=['POST'])
@login.login_required
def done(type_name: str, task_id: str) -> Response:
    """
    This action adds the task to the 'skipped' list of current user.

    :param type_name: Task type name
    :type type_name: str
    :param task_id: Task ID
    :type task_id: str

    :returns: Prepared response.
    :rtype: Response
    """
    user = flask.g.user
    task_type = utils.resolve_task_type(type_name, TASKS_TYPES, user)

    if task_type is None:
        return NO_TASKS

    try:
        task_type.on_task_done(
            user, task_id, json.loads(flask.request.form.get('result')))
    except TaskNotFoundError:
        return NO_TASKS

    return utils.json_response({'done': True})


# endregion Views


# region Filters
@app.template_filter('strip_email')
def strip_email(s: str) -> str:
    """
    Filter which extracts the first part of an email to make an shorthand
    for user.

    :param s: Input email (or any string).
    :type s: str
    :return: A shorthand extracted.
    :rtype: str
    """
    return s.split('@', 1)[0]


@app.template_filter('app_template')
def app_template_filter(s: str) -> str:
    """
    Looks for the full path for given template.

    :param s: Template name.
    :type s: str

    :return: Full path to the template
    :rtype: str
    """
    return utils.get_template_path(app, s)


# endregion Filters


# region Context processors
@app.context_processor
def is_initialized() -> Dict[str, bool]:
    """
    Extends the context with the flag showing that the application DB was
    successfully initialized.

    :return: a dict with the `init` flag
    :rtype: Dict[str, bool]
    """
    return {
        'init': cli.is_initialized()
    }
# endregion Context processors
