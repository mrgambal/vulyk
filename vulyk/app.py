# -*- coding: utf-8 -*-
import httplib
import ujson as json

from flask import (Flask, render_template, redirect, url_for, g, request,
                   Response, abort)
from flask.ext import login
from flask.ext.mongoengine import MongoEngine

from vulyk import cli
from vulyk.assets import init as assets_init
from vulyk.tasks import init_tasks
from vulyk.users import init_social_login
from vulyk.utils import resolve_task_type

app = Flask(__name__)
app.config.from_object('vulyk.settings')

assets_init(app)
db = MongoEngine(app)
init_social_login(app, db)
TASKS_TYPES = init_tasks(app)


def _json_response(result, template="", errors=None, status=httplib.OK):
    """
    Handy helper to prepare unified responses

    :param result: Data to be sent
    :type result: dict
    :param template: Template name or id
    :type template: str | unicode
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
        "result": result,
        "template": template,
        "errors": errors})

    return Response(data, status, mimetype='application/json')

_no_tasks = _json_response({}, "",
                           ["There is no task having type like this"],
                           httplib.NOT_FOUND)


@app.route('/', methods=["GET"])
def index():
    """
    Main site view
    """
    if g.user.is_authenticated():
        task_types = [t for t in TASKS_TYPES.keys()
                      if g.user.is_eligible_for(t)]
    else:
        task_types = []

    return render_template("index.html",
                           task_types=task_types,
                           init=cli.is_initialized())


@app.route('/types', methods=['GET'])
@login.login_required
def types():
    """
    Produces a list of available tasks types which are appropriate
    for current user.
    """
    res = [t for t in TASKS_TYPES.keys() if g.user.is_eligible_for(t)]

    return _json_response({"types": res})


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()

    return redirect(url_for('index'))


@app.route('/type/<string:type_name>/next', methods=["GET"])
@login.login_required
def next(type_name):
    """
    Provides next available task for user.
    If user isn't eligible for that type of tasks - an exception
    should be thrown.

    :param type_name: Task type name
    :type type_name: basestring
    """
    task_type = resolve_task_type(type_name, g.user)

    if task_type is None:
        return _no_tasks

    task = task_type.get_next(g.user)

    if not task:
        return _no_tasks

    return _json_response(
        {"task": task},
        # doubtful that we need it.
        task_type.template
    )


@app.route('/type/<string:type_name>/', methods=["GET"])
@login.login_required
def task_home(type_name):
    """
    :param type_name: Task type name
    :type type_name: basestring
    """
    task_type = resolve_task_type(type_name, g.user)

    if task_type is None:
        abort(httplib.NOT_FOUND)

    return render_template("task.html", task_type=task_type)


@app.route('/type/<string:type_name>/skip/<string:task_id>', methods=["POST"])
@login.login_required
def skip(type_name, task_id):
    """
    This action adds the task to the 'skipped' list of current user.

    :param type_name: Task type name
    :type type_name: basestring
    :param task_id: Task ID
    :type task_id: basestring
    """
    task_type = resolve_task_type(type_name, g.user)

    if task_type is None:
        return _no_tasks

    task_type.skip_task(user=g.user._get_current_object(), task_id=task_id)
    return _json_response({"done": True})


@app.route('/type/<string:type_name>/done/<string:task_id>', methods=["POST"])
@login.login_required
def done(type_name, task_id):
    """
    This action adds the task to the 'skipped' list of current user.

    :param type_name: Task type name
    :type type_name: basestring
    :param task_id: Task ID
    :type task_id: basestring
    """

    task_type = resolve_task_type(type_name, g.user)

    if task_type is None:
        return _no_tasks

    task_type.on_task_done(
        # Mongoengine will shit bricks if it'll receive LocalProxy object
        g.user._get_current_object(),
        task_id, json.loads(request.form.get("result")))

    return _json_response({"done": True})
