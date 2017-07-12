# -*- coding: utf-8 -*-
from vulyk.blueprints.gamification.models.task_types import \
    AbstractGamifiedTaskType

from ..fixtures import FakeModel, FakeAnswer


class FakeType(AbstractGamifiedTaskType):
    task_model = FakeModel
    answer_model = FakeAnswer
    type_name = 'FakeGamifiedTaskType'
    template = 'tmpl.html'

    _name = 'Fake name'
    _description = 'Fake description'
