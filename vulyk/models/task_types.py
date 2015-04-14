# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from hashlib import sha1
from operator import itemgetter
import random
import six
import ujson as json

from mongoengine.errors import (
    InvalidQueryError,
    LookUpError,
    NotUniqueError,
    OperationError,
    ValidationError
)

from vulyk.models.tasks import AbstractTask, AbstractAnswer
from vulyk.models.user import User
from vulyk.models.exc import (
    TaskImportError,
    TaskSaveError,
    TaskSkipError,
    TaskValidationError,
    WorkSessionLookUpError
)
from vulyk.models.stats import WorkSession
from vulyk.utils import get_tb


class AbstractTaskType(object):
    answer_model = None
    task_model = None

    _name = ''
    _description = ''

    template = ''
    helptext_template = ''
    type_name = ''

    redundancy = 3
    JS_ASSETS = []
    CSS_ASSETS = []

    def __init__(self, settings):
        assert issubclass(self.task_model, AbstractTask), \
            'You should define task_model property'

        assert issubclass(self.answer_model, AbstractAnswer), \
            'You should define answer_model property'

        assert self.type_name, 'You should define type_name (underscore)'
        assert self.template, 'You should define template'

    @property
    def name(self):
        return self._name if len(self._name) > 0 else self.type_name

    @property
    def description(self):
        return self._description if len(self._description) > 0 else ''

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
            raise TaskImportError('Can\'t load task: {0}'.format(e))

    def export_reports(self, closed=True, qs=None):
        """Exports results
        io is left out of scope here as well

        Args:
            qs: Queryset, an optional argument. Default value is QS that
            exports all tasks with amount of answers > redundancy
        Returns:
            Generator of lists of dicts with results
        """

        if qs is None:
            # Not really tested yet
            qs = self.task_model.objects(closed=closed)

        for task in qs:
            yield [answer.as_dict()
                   for answer in self.answer_model.objects(task=task)]

    def get_leaders(self):
        """Return sorted list of tuples (user_id, tasks_done)

        :returns: list of tuples (user_id, tasks_done)
        :rtype: list
        """
        scores = self.answer_model.objects.item_frequencies('created_by')
        return sorted(scores.items(), key=itemgetter(1), reverse=True)

    def get_leaderboard(self, limit=10):
        """Find users who contributed the most

        :param limit: number of top users to return
        :type limit: integer

        :returns: List of dicts {user: user_obj, freq: count}
        :rtype: list
        """

        # TODO: Here we should filter answers by task_type, which is absent atm
        scores = self.get_leaders()

        return map(lambda x: {"user": User.objects.get(id=x[0]),
                              "freq": x[1]}, scores[:limit])

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
            # Not sure if we should do that here on GET requests
            self._start_work_session(task, user.id)

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

        if rs.count() == 0:
            # loosening restrictions here
            rs = self.task_model.objects(
                task_type=self.type_name,
                users_processed__ne=user.id,
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
            task = self.task_model.objects.get_or_404(
                id=task_id, task_type=self.type_name)
            task.update(push__users_skipped=user)
            self._del_work_session(task, user)
        except NotUniqueError as err:
            raise TaskSkipError(six.text_type(err))
        except OperationError as err:
            raise TaskSkipError('Can not skip the task: {0}'.format(err))

    def on_task_done(self, user, task_id, result):
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
                .get_or_404(id=task_id, task_type=self.type_name)  # TODO: exc
            answer, _ = self.answer_model \
                .objects \
                .get_or_create(task=task, created_by=user.id)

            answer.update(set__result=result)
            # update task
            self._update_task_on_answer(task, answer, user)
            # update user
            user.update(inc__processed=1)
            # update stats record
            self._end_work_session(task, user.id, answer)
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
        return False

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

        if self._is_ready_for_autoclose(task, answer):
            task.closed = True
        else:
            task.closed = task.users_count >= self.redundancy

        task.save()

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
            rs.first().update(
                set__end_time=datetime.now(),
                set__answer=answer,
                set__corrections=answer.corrections)
        else:
            msg = 'No session was found for {0}'.format(answer)

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
            msg = 'No session was found for {0} & {1}'.format(user, task.id)

            raise WorkSessionLookUpError(msg)

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type_name
        }
