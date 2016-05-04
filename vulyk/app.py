# -*- coding: utf-8 -*-
import ujson as json

import flask
from flask import (Flask, Response)
import flask_login as login
from flask_mongoengine import MongoEngine

from vulyk import cli
from vulyk.assets import init as assets_init
from vulyk.tasks import init_tasks
from vulyk.users import init_social_login
from vulyk.utils import resolve_task_type, HTTPStatus, get_template_path

app = Flask(__name__)
app.config.from_object('vulyk.settings')
app.config.from_object('local_settings')
db = MongoEngine(app)

assets_init(app)
init_social_login(app, db)

TASKS_TYPES = init_tasks(app)


@app.template_filter('app_template')
def app_template_filter(s):
    return get_template_path(app, s)


@app.context_processor
def is_initialized():
    return {
        'init': cli.is_initialized()
    }


def _json_response(result, template='', errors=None, status=HTTPStatus.OK):
    """
    Handy helper to prepare unified responses

    :param result: Data to be sent
    :type result: dict
    :param template: Template name or id
    :type template: str
    :param errors: List of errors
    :type errors: list | set | tuple | dict
    :param status: Response http-status
    :type status: int

    :returns: Jsonified response
    :rtype: Response
    """
    if not errors:
        errors = []

    data = json.dumps({
        'result': result,
        'template': template,
        'errors': errors})

    return Response(
        data, status, mimetype='application/json',
        headers=[
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
            ('Pragma', 'no-cache'),
            ('Expires', '0'),
        ])


_no_tasks = _json_response({}, '', ['There is no task having type like this'],
                           HTTPStatus.NOT_FOUND)


@app.route('/', methods=['GET'])
def index():
    """
    Main site view
    """
    task_types = []
    user = flask.g.user

    if user.is_authenticated:
        task_types = [x.to_dict() for x in TASKS_TYPES.values()
                      if user.is_eligible_for(x.type_name)]

    if len(task_types) == 1:
        return flask.redirect(
            flask.url_for('task_home', type_name=task_types[0]['type']))

    return flask.render_template(get_template_path(app, 'index.html'),
                                 task_types=task_types)


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()

    return flask.redirect(flask.url_for('index'))


@app.route('/type/<string:type_name>/next', methods=['GET'])
@login.login_required
def next_page(type_name):
    """
    Provides next available task for user.
    If user isn't eligible for that type of tasks - an exception
    should be thrown.

    :param type_name: Task type name
    :type type_name: str
    """
    user = flask.g.user
    task_type = resolve_task_type(type_name, TASKS_TYPES, user)

    if task_type is None:
        return _no_tasks

    task = task_type.get_next(user)

    if not task:
        return _no_tasks

    return _json_response(
        {
            'task': task,
            'stats': user.get_stats(task_type=task_type)
        },
        # doubtful that we need it.
        task_type.template
    )


@app.route('/type/<string:type_name>/', methods=['GET'])
@login.login_required
def task_home(type_name):
    """
    :param type_name: Task type name
    :type type_name: str
    """
    task_type = resolve_task_type(type_name, TASKS_TYPES, flask.g.user)

    if task_type is None:
        flask.abort(HTTPStatus.NOT_FOUND)

    return flask.render_template(get_template_path(app, 'task.html'),
                                 task_type=task_type)


@app.route('/type/<string:type_name>/leaders', methods=['GET'])
@login.login_required
def leaders(type_name):
    """
    :param type_name: Task type name
    :type type_name: str
    """
    task_type = resolve_task_type(type_name, TASKS_TYPES, flask.g.user)

    if task_type is None:
        flask.abort(HTTPStatus.NOT_FOUND)

    return flask.render_template(
        get_template_path(app, 'leaderboard.html'),
        task_type=task_type,
        leaders=task_type.get_leaderboard())


@app.route('/type/<string:type_name>/skip/<string:task_id>', methods=['POST'])
@login.login_required
def skip(type_name, task_id):
    """
    This action adds the task to the 'skipped' list of current user.

    :param type_name: Task type name
    :type type_name: str
    :param task_id: Task ID
    :type task_id: str
    """
    user = flask.g.user
    task_type = resolve_task_type(type_name, TASKS_TYPES, user)

    if task_type is None:
        return _no_tasks

    task_type.skip_task(user=user._get_current_object(),
                        task_id=task_id)
    return _json_response({'done': True})


@app.route('/type/<string:type_name>/done/<string:task_id>', methods=['POST'])
@login.login_required
def done(type_name, task_id):
    """
    This action adds the task to the 'skipped' list of current user.

    :param type_name: Task type name
    :type type_name: str
    :param task_id: Task ID
    :type task_id: str
    """
    user = flask.g.user
    task_type = resolve_task_type(type_name, TASKS_TYPES, user)

    if task_type is None:
        return _no_tasks

    task_type.on_task_done(
        # Mongoengine will shit bricks if it'll receive LocalProxy object
        user._get_current_object(),
        task_id, json.loads(flask.request.form.get('result')))

    return _json_response({'done': True})


@app.template_filter('strip_email')
def strip_email(s):
    return s.split('@', 1)[0]
