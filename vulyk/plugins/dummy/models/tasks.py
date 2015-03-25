# -*- coding: utf-8 -*-
from vulyk.models.tasks import AbstractTask, AbstractAnswer


class DummyTask(AbstractTask):
    pass


class DummyAnswer(AbstractAnswer):
    def corrections(self):
        return 0
