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
        return self.task_model().as_dict()

    def save_task_result(self, user, task_id, result):
        """Saves user's answers for a given task
        Stub for DummyTaskType

        :param user: an instance of User model who provided an answer
        :type user: models.User
        :param task_id: Given task ID
        :type task_id: basestring
        :param result: Task solving result
        :type result: dict

        :raises: TaskSaveError - in case of general problems
        :raises: TaskValidationError - in case of validation problems
        """
        return True
