# -*- coding: utf-8 -*-
import os

from flask import Flask, render_template, redirect, request, url_for, jsonify, g
from flask.ext import login
from flask.ext.mongoengine import MongoEngine

from assets import init as assets_init
from models.repositories import TaskRepository, ReportRepository
from users import init_social_login

app = Flask(__name__)
app.config.from_object('settings')

try:
    app.config.from_object('local_settings')
except ImportError:
    pass

assets_init(app)
db = MongoEngine(app)
init_social_login(app, db)


@app.route('/logout', methods=['POST'])
def logout():
    login.logout_user()

    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/next', methods=["POST"])
@login.login_required
def next():
    redundancy = app.config.get('USERS_PER_TASK', 2)
    task = TaskRepository.get_instance().get_next_task(g.user, redundancy)

    return (request.is_xhr
            and jsonify({"task": task}), 200
            or render_template("_task.html", task=task))


@app.route('/report', methods=["POST"])
@login.login_required
def report():
    res = TaskRepository.get_instance() \
        .save_on_success(request.values, g.user)
    res = ReportRepository.get_instance() \
        .create(res, g.user, request.values.get("mistakes", {}))

    return jsonify({"ok": res}), res and 200 or 500


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
