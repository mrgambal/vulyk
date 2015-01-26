import random
import ujson as json
from hashlib import sha1
from mongoengine.errors import OperationError, NotUniqueError

from .exc import TaskSkipError, TaskImportError
from .tasks import AbstractTask


class AbstractTaskType(object):
    task_model = None
    redundancy = 2

    def __init__(self, redundancy):
        self.redundancy = redundancy

        assert issubclass(self.task_model, AbstractTask), \
            "You should define task_model property"

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
            users_count__lt=self.redundancy,
            users_processed__ne=user.id,
            users_skipped__ne=user.id)
        res = res[random.randint(0, res.count())]

        return res.as_dict()

    def skip_task(self, user, task):
        """Marks given task as a skipped by a given user
        Assumes that user is eligible for this kind of tasks

        Args:
            user: an instance of User model
            task: an instance of self.task_model model
        Returns:
            None

        Raises:
            TaskSkipError
        """
        try:
            self.task_model \
                .objects(id=task.id) \
                .update_one(push__users_skipped=user)
        except NotUniqueError as err:
            raise TaskSkipError(unicode(err))
        except OperationError as err:
            raise TaskSkipError(u"Can not skip the task: {0}".format(err))

    def save_task_result(self, user, task, answer):
        """Saves user's answers for a given task
        Assumes that user is eligible for this kind of tasks
        Covers both, add and update (when user is editing his results) cases

        Args:
            user: an instance of User model who provided an answer
            task: an instance of self.task_model model
            answer: QueryDict with answers
        Returns:
            True if succeed, otherwise - False

        Raises:
            TaskSaveError - in case of general problems
            TaskValidationError - in case of validation problems
        """

        user.update(inc__processed=1)
        task.update(inc__users_count=1, push__users_processed=user)
        # TODO: Gotta think more.
        raise NotImplementedError

    # Still in doubts about these methods:
    # get_media that returns js/css specific for a task. Might as well go
    # to a TaskType property or be mentioned right in template
    #
    # get_help that returns help text or template with help. Might be a
    # property too
    #
    # edit, that will return qs or a paginated list of tasks that was already
    # complete by a given user or None if editing is prohibited for this task
    # type
