# -*- coding: utf-8 -*-
import httplib
from flask import Flask, render_template, redirect, url_for, g, abort
from flask.ext import login
from flask.ext.mongoengine import MongoEngine

from .assets import init as assets_init
from .users import init_social_login
from .utils import resolve_task_type
from .tasks import init_tasks

app = Flask(__name__)
app.config.from_object('vulyk.settings')

assets_init(app)
db = MongoEngine(app)
init_social_login(app, db)
TASKS_TYPES = init_tasks(app)


@app.route('/', methods=["GET"], defaults={'type_name': None})
@app.route('/type/<string:type_name>', methods=["GET"])
def index(type_name):
    """
    Main site view
    Task type selection (not implemented)

    :param type_name: Task type name
    :type type_name: basestring
    """
    if type_name:
        task_type = resolve_task_type(type_name, g.user)

        if task_type is not None:
            return redirect(url_for('next', type_name=type_name))
    else:
        return render_template("index.html", type_name=type_name)


@app.route('/type', methods=['GET'])
def types():
    """
    Produces a selectable list of available tasks which are appropriate
    for current user.
    """
    # TODO: need a template
    return render_template('types.html', types=TASKS_TYPES.keys())


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()

    return redirect(url_for('index'))


@app.route('/next', methods=["GET"], defaults={'type_name': None})
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

        return render_template(task_type.template, task=task)
    else:
        # http://goo.gl/LhxvJd
        return redirect(url_for('index', type_name=type_name))


@app.route('/skip/<string:task_id>', methods=["GET"],
           defaults={'type_name': None})
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
        task = task_type.task_model.objects.get_or_404(id=task_id)
        task_type.skip_task(user=g.user, task=task)

        return redirect(url_for('next', type_name=type_name))
    else:
        abort(httplib.NOT_FOUND)
