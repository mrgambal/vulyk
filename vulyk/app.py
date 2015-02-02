# -*- coding: utf-8 -*-
import httplib
import ujson as json
from flask import (Flask, render_template, redirect, url_for, g, request,
                   Response)
from flask.ext import login
from flask.ext.mongoengine import MongoEngine

from vulyk.assets import init as assets_init
from vulyk.users import init_social_login
from vulyk.utils import resolve_task_type
from vulyk.tasks import init_tasks

app = Flask(__name__)
app.config.from_object('vulyk.settings')

assets_init(app)
db = MongoEngine(app)
init_social_login(app, db)
TASKS_TYPES = init_tasks(app)


@app.route('/', methods=["GET"])
def index():
    """
    Main site view
    """
    return render_template("index.html")


@app.route('/types', methods=['GET'])
def types():
    """
    Produces a list of available tasks types which are appropriate
    for current user.
    """
    res = [t for t in TASKS_TYPES.keys() if g.user.is_eligible_for(t)]
    data = json.dumps({
        "result": {"types": res},
        "template": "",
        "errors": []})

    return Response(data, httplib.OK)


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

    if task_type is not None:
        task = task_type.get_next(g.user)
        data = json.dumps({
            "result": {"task": task},
            "template": task_type.template,
            "errors": [] if task else ["There is no task for you"]})

        return Response(data, httplib.OK)
    else:
        data = json.dumps({
            "result": {},
            "template": "",
            "errors": ["There is no task having type like this"]})

        return Response(data, httplib.NOT_FOUND)


@app.route('/type/<string:type_name>/skip/<string:task_id>', methods=["GET"])
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

    if task_type is not None:
        task_type.skip_task(user=g.user, task_id=task_id)

        data = json.dumps({
            "result": {"done": True},
            "template": "",
            "errors": []})

        return Response(data, httplib.OK)
    else:
        data = json.dumps({
            "result": {},
            "template": "",
            "errors": ["There is no task having type like this"]})

        return Response(data, httplib.NOT_FOUND)


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

    if task_type is not None:
        task_type.on_task_done(g.user, task_id, request.form.get("result"))

        data = json.dumps({
            "result": {"done": True},
            "template": "",
            "errors": []})

        return Response(data, httplib.OK)
    else:
        data = json.dumps({
            "result": {},
            "template": "",
            "errors": ["There is no task having type like this"]})

        return Response(data, httplib.NOT_FOUND)
