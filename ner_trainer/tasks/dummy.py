from ner_trainer.models.task_types import AbstractTaskType
from ner_trainer.models.tasks import AbstractTask


class DummyTask(AbstractTask):
    pass


class DummyTaskType(AbstractTaskType):
    task_model = DummyTask
    type_name = "dummy_task"
    template = "dummy_template.html"
