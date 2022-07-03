# -*- coding: utf-8 -*-
from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractAnswer, AbstractTask


class FakeModel(AbstractTask):
    pass


class FakeAnswer(AbstractAnswer):
    pass


class FakeType(AbstractTaskType):
    task_model = FakeModel
    answer_model = FakeAnswer
    type_name = 'FakeTaskType'
    template = 'tmpl.html'

    _name = 'Fake name'
    _description = 'Fake description'
