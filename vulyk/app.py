# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, g
from flask.ext import login
from flask.ext.mongoengine import MongoEngine

from assets import init as assets_init
from users import init_social_login
from utils import resolve_task_type
from tasks import init_tasks

app = Flask(__name__)
app.config.from_object('vulyk.settings')

try:
    app.config.from_object('vulyk.local_settings')
except ImportError:
    pass


assets_init(app)
db = MongoEngine(app)
init_social_login(app, db)
TASKS_TYPES = init_tasks(app)


@app.route('/', methods=["GET"], defaults={'task_type': None})
@app.route('/type/<string:task_type>/', methods=["GET"])
@resolve_task_type
def index(task_type):
    return render_template("index.html", task_type=task_type)


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()

    return redirect(url_for('index'))


@app.route('/next', methods=["GET"], defaults={'task_type': None})
@app.route('/type/<string:task_type>/next', methods=["GET"])
@resolve_task_type
@login.login_required
def next(task_type):
    """
    Provides next available task for user.

    :type task_type: AbstractTaskType
    """
    task = task_type.get_next(g.user)

    # still not sure about necessity of rendering by *TaskType

    # template = request.is_xhr and "_task.html" or "task.html"
    # return render_template(template, task=task)
    return "Hello world"


@app.route('/skip/<string:task_id>', methods=["GET"],
           defaults={'task_type': None})
@app.route('/type/<string:task_type>/skip/<string:task_id>', methods=["GET"])
@resolve_task_type
@login.login_required
def skip(task_type, task_id):
    """
    This action adds the task to 'skipped' list of current user.

    :type task_type: AbstractTaskType
    :type task_id: str | unicode
    """
    task_type.skip_task(g.user,
                        task_type.task_model.objects.get_or_404(id=task_id))

    redirect(url_for('next'))

# Decorator Hell is coming.
