# coding=utf-8
import random
import ujson as json
from datetime import datetime
from hashlib import sha1
from mongoengine.errors import (OperationError, NotUniqueError, LookUpError,
                                ValidationError, InvalidQueryError)

from vulyk.models import AbstractTask, AbstractAnswer, WorkSession
from vulyk.models.exc import (
    TaskSkipError, TaskImportError, TaskValidationError, TaskSaveError,
    WorkSessionLookUpError)
from vulyk.utils import get_tb


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

        assert issubclass(self.answer_model, AbstractAnswer), \
            "You should define answer_model property"

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
        """
        Finds given user a new task and starts new WorkSession

        :param user: an instance of User model
        :type user: models.User

        :returns: Prepared dictionary of model, or empty dictionary
        :rtype: dict
        """
        task = self._get_next_task(user)

        if task is not None:
            self._start_work_session(task, user)

            return task.as_dict()
        else:
            return {}

    def _get_next_task(self, user):
        """
        Finds given user a new task

        :param user: an instance of User model
        :type user: models.User

        :returns: Model instance or None
        :rtype: AbstractTask
        """
        task = None
        rs = self.task_model.objects(
            task_type=self.type_name,
            users_processed__ne=user.id,
            users_skipped__ne=user.id,
            closed__ne=True)

        if rs.count() > 0:
            task = random.choice(rs)

        return task

    def skip_task(self, task_id, user):
        """
        Marks given task as a skipped by a given user
        Assumes that user is eligible for this kind of tasks

        :param task_id: Given task ID
        :type task_id: basestring
        :param user: an instance of User model who provided an answer
        :type user: models.User

        :raises: TaskSkipError
        """
        try:
            task = self.task_model.objects.get_or_404(id=task_id,
                                                      type=self.type_name)
            task.update(push__users_skipped=user)
            self._del_work_session(task, user)
        except NotUniqueError as err:
            raise TaskSkipError(unicode(err))
        except OperationError as err:
            raise TaskSkipError(u"Can not skip the task: {0}".format(err))

    def on_task_done(self, task_id, user, result):
        """
        Saves user's answers for a given task
        Assumes that user is eligible for this kind of tasks
        Covers both, add and update (when user is editing his results) cases

        :param task_id: Given task ID
        :type task_id: basestring
        :param user: an instance of User model who provided an answer
        :type user: models.User
        :param result: Task solving result
        :type result: dict

        :raises: TaskSaveError - in case of general problems
        :raises: TaskValidationError - in case of validation problems
        """
        try:
            # create new answer or modify existing one
            task = self.task_model \
                .objects \
                .get_or_404(id=task_id, type=self.type_name)
            answer = self.answer_model \
                .objects \
                .get_or_create(task=task, created_by=user) \
                .update(set__result=result)
            # update task
            self._update_task_on_answer(task, answer, user)
            # update user
            user.update(inc__processed=1)
            # update stats record
            self._end_work_session(task, user, answer)
        except ValidationError as err:
            raise TaskValidationError(err, get_tb())
        except (OperationError, LookUpError, InvalidQueryError) as err:
            raise TaskSaveError(err, get_tb())

    def _is_ready_for_autoclose(self, task, answer):
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

    # TODO: make up something prettier than that mess
    def _start_work_session(self, task, user):
        """
        Starts new WorkSession

        :param task: Given task
        :type task: AbstractTask
        :param user: an instance of User model who gets new task
        :type user: models.User
        """
        WorkSession.objects.create(user=user, task=task)

    def _end_work_session(self, task, user, answer):
        """
        Ends current WorkSession

        :param task: Given task
        :type task: AbstractTask
        :param user: an instance of User model who gets new task
        :type user: models.User
        :param answer: Given answer
        :type answer: AbstractAnswer

        :raises: WorkSessionLookUpError - if session was not found
        """
        # TODO: store id of active session in cookies or elsewhere
        rs = WorkSession.objects(user=user, task=task).order_by('-start_time')

        if rs.count() > 0:
            rs.first() \
                .update(
                set__end_time=datetime.now(),
                set__answer=answer,
                set__corrections=answer.corrections)
        else:
            msg = "No session was found for {0}".format(answer)

            raise WorkSessionLookUpError(msg)

    def _del_work_session(self, task, user):
        """
        Deletes current WorkSession if skipped

        :param task: Given task
        :type task: AbstractTask
        :param user: an instance of User model who gets new task
        :type user: models.User

        :raises: WorkSessionLookUpError - if session was not found
        """
        rs = WorkSession.objects(user=user, task=task).order_by('-start_time')

        if rs.count() > 0:
            rs.first().delete()
        else:
            msg = "No session was found for {0} & {1}".format(user, task.id)

            raise WorkSessionLookUpError(msg)
