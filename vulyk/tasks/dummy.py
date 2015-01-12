from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractTask


class DummyTask(AbstractTask):
    pass


class DummyTaskType(AbstractTaskType):
    task_model = DummyTask
    type_name = "dummy_task"
    template = "dummy_template.html"

    def export_reports(self, qs=None):
        """Exports results
        Stub for DummyTaskType

        Args:
            qs: Queryset, an optional argument. Default value is QS that
            exports all tasks with amount of answers > redundancy
        Returns:
            Generator with empty dict
        """

        yield {}

    def get_next(self, user):
        """Finds given user a new task
        Stub for DummyTaskType

        Args:
            user: an instance of User model
        Returns:
            empty string
        """
        return self._render_task(self.task_model())

    def _render_task(self, task):
        """Returns rendered self.template with values from task inserted
        Stub for DummyTaskType

        Args:
            task: an instance of self.task_model model
        Returns:
            empty string
        """
        return ""

    def save_task_result(self, user, task, answer):
        """Saves user's answers for a given task
        Stub for DummyTaskType

        Args:
            user: an instance of User model who provided an answer
            task: an instance of self.task_model model
            answer: QueryDict with answers
        Returns:
            always True

        Raises:
            TaskSaveError - in case of general problems
            TaskValidationError - in case of validation problems
        """
        return True
