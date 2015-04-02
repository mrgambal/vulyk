# coding=utf-8
from vulyk.models.task_types import AbstractTaskType
from vulyk.plugins.dummy.models.tasks import DummyTask, DummyAnswer


class DummyTaskType(AbstractTaskType):
    task_model = DummyTask
    answer_model = DummyAnswer

    type_name = "dummy_task"
    template = "base.html"

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

    def on_task_done(self, user, task_id, result):
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
        pass

    def _is_ready_for_autoclose(self, answer, task):
        """
        Returns count of the same answers for autocloseable tasks.

        Example implementation

        :param task: an instance of self.task_model model
        :type task: AbstractTask
        :param answer: Task solving result
        :type answer: AbstractAnswer

        :returns: How many identical answers we got
        :rtype: int
        """
        auto_close_redundancy = 2

        rs = self.answer_model.objects(task=task)
        identical = len([x for x in rs if x == answer])

        return identical == auto_close_redundancy
