# -*- coding: utf-8 -*-
from ..fixtures import FakeModel, FakeAnswer
from vulyk.blueprints.gamification.models.task_types import AbstractGamifiedTaskType


class FakeType(AbstractGamifiedTaskType):
    task_model = FakeModel
    answer_model = FakeAnswer
    type_name = 'FakeTaskType'
    template = 'tmpl.html'

    _name = 'Fake name'
    _description = 'Fake description'
