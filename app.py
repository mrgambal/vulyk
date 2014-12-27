# -*- coding: utf-8 -*-
from flask import (Flask, render_template, redirect, request, url_for, g,
                   jsonify)
from flask.ext import login
from flask.ext.mongoengine import MongoEngine

from assets import init as assets_init
# from models.repositories import TaskRepository, ReportRepository
from users import init_social_login
from utils import resolve_task_type
from tasks import init_tasks

app = Flask(__name__)
app.config.from_object('settings')

try:
    app.config.from_object('local_settings')
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
@login.login_required
def next(task_type):
    # redundancy = app.config.get("USERS_PER_TASK", 2)
    # task = TaskRepository.get_instance().get_next_task(g.user, redundancy)
    # template = request.is_xhr and "_task.html" or "task.html"

    # return render_template(template, task=task)
    return "Hello world"


# @app.route('/report', methods=["POST"])
# @login.login_required
# def report():
#     res = TaskRepository.get_instance() \
#         .save_on_success(request.values, g.user)
#     res = ReportRepository.get_instance() \
#         .create(res, g.user, request.values.get("mistakes", {}))

#     return jsonify({"ok": res}), res and 200 or 500
