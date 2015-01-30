# coding=utf-8
import random
import ujson as json
from hashlib import sha1
from mongoengine.errors import OperationError, NotUniqueError

from .exc import TaskSkipError, TaskImportError
from .tasks import AbstractTask, AbstractAnswer


class AbstractTaskType(object):
    answer_model = None
    task_model = None

    template = ""
    type_name = ""

    redundancy = 3

    def __init__(self, redundancy):
        self.redundancy = redundancy

        assert issubclass(self.task_model, AbstractTask), \
            "You should define task_model property"
        # I'm too exhausted to understand why it doesn't work =(
        #
        # assert issubclass(self.answer_model, AbstractAnswer), \
        # "You should define answer_model property"

        assert self.type_name, "You should define type_name (underscore)"
        assert self.template, "You should define template"

    def import_tasks(self, tasks):
        """Imports tasks from an iterable over dicts
        io is left out of scope here.

        Args:
            tasks: An iterable over dicts
        Returns:
            None

        Raises:
            TaskImportError
        """
        try:
            for task in tasks:
                self.task_model.objects.create(
                    _id=sha1(json.dumps(task)).hexdigest()[:20],
                    task_type=self.type_name,
                    task_data=task
                )
        except (AttributeError, TypeError, OperationError) as e:
            # TODO: review list of exceptions, any fallback actions if needed
            raise TaskImportError(u"Can't load task: {0}".format(e))

    def export_reports(self, qs=None):
        """Exports results
        io is left out of scope here as well

        Args:
            qs: Queryset, an optional argument. Default value is QS that
            exports all tasks with amount of answers > redundancy
        Returns:
            Generator of dicts with results
        """

        if qs is None:
            # Not really tested yet
            qs = self.task_model.objects.filter(
                users_count__gte=self.redundancy)

        for task in qs:
            yield task.get_results()

    def get_next(self, user):
        """Finds given user a new task
        Assumes that user is eligible for this kind of tasks

        Args:
            user: an instance of User model
        Returns:
            Prepared dictionary or model, or None

        Raises:
            TaskPermissionError
        """
        res = self.task_model.objects(
            task_type=self.type_name,
            users_processed__ne=user.id,
            users_skipped__ne=user.id,
            closed__ne=True)
        res = res[random.randint(0, res.count())]

        return res.as_dict()

    def skip_task(self, user, task_id):
        """
        Marks given task as a skipped by a given user
        Assumes that user is eligible for this kind of tasks

        :param user: an instance of User model who provided an answer
        :type user: models.User
        :param task_id: Given task ID
        :type task_id: basestring

        :raises: TaskSkipError
        """
        try:
            self.task_model.objects \
                .get_or_404(id=task_id) \
                .update(push__users_skipped=user)
        except NotUniqueError as err:
            raise TaskSkipError(unicode(err))
        except OperationError as err:
            raise TaskSkipError(u"Can not skip the task: {0}".format(err))

    def on_task_done(self, user, task_id, result):
        """
        Saves user's answers for a given task
        Assumes that user is eligible for this kind of tasks
        Covers both, add and update (when user is editing his results) cases

        :param user: an instance of User model who provided an answer
        :type user: models.User
        :param task_id: Given task ID
        :type task_id: basestring
        :param result: Task solving result
        :type result: dict

        :raises: TaskSaveError - in case of general problems
        :raises: TaskValidationError - in case of validation problems
        """
        # create new answer or modify existing one
        task = self.task_model \
            .objects \
            .get_or_404(id=task_id)
        answer = self.answer_model \
            .objects \
            .get_or_create(task=task, created_by=user) \
            .update(set__result=result)
        # update task
        self._update_task_on_answer(task, answer, user)
        # update user
        user.update(inc__processed=1)

    def _is_ready_for_autoclose(self, answer, task):
        """
        Checks if task could be closed before it
        Should be overridden if you need more complex logic.

        :param task: an instance of self.task_model model
        :type task: AbstractTask
        :param answer: Task solving result
        :type answer: AbstractAnswer

        :returns: How many identical answers we got
        :rtype: bool
        """
        raise NotImplementedError()

    def _update_task_on_answer(self, task, answer, user):
        """
        Sets flag 'closed' to True if task's goal has been reached

        :param task: an instance of self.task_model model
        :type task: AbstractTask
        :param answer: Task solving result
        :type answer: AbstractAnswer
        :param user: an instance of User model who provided an answer
        :type user: models.User
        """
        task.users_count += 1
        task.users_processed.append(user)

        if self._is_ready_for_autoclose(answer, task):
            task.closed = True
        else:
            task.closed = task.users_count == self.redundancy

        task.save()

        # get_help that returns help text or template with help. Might be a
        # property too
        #
        # edit, that will return qs or a paginated list of tasks that was already
        # complete by a given user or None if editing is prohibited for this task
        # type
