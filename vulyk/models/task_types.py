# -*- coding: utf-8 -*-
"""Module contains all models related to task type (plugin root) entity."""

from datetime import datetime
from hashlib import sha1
import logging
import random
import ujson as json

from mongoengine import Q
from mongoengine.errors import (
    InvalidQueryError,
    LookUpError,
    NotUniqueError,
    OperationError,
    ValidationError
)

from vulyk.ext.leaderboard import LeaderBoardManager
from vulyk.ext.worksession import WorkSessionManager
from vulyk.models.exc import (
    TaskImportError,
    TaskSaveError,
    TaskSkipError,
    TaskValidationError,
    TaskNotFoundError
)
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractTask, AbstractAnswer, Batch
from vulyk.models.user import User
from vulyk.utils import get_tb

__all__ = [
    'AbstractTaskType'
]


class AbstractTaskType:
    """
    The main entity in the application. Contains all the logic we need to
    handle task emission/accounting.

    Could be overridden in plugins to fit your needs.

    The simplest and most common scenario of being overridden is to have own
     task type name and description to separate your tasks from any other.
    """
    # models
    answer_model = None
    task_model = None

    template = ''
    helptext_template = ''
    type_name = ''

    redundancy = 3
    JS_ASSETS = []
    CSS_ASSETS = []

    # properties
    _name = ''
    _description = ''

    # Meta information on project to copy to task batches
    _task_type_meta = {}

    # managers
    _work_session_manager = None
    _leaderboard_manager = None

    def __init__(self, settings):
        """
        Constructor.

        :param settings: We pass global settings dictionary into the
        constructor when instantiating plugins. Could be useful for plugins.
        :type settings: dict
        """
        self._logger = logging.getLogger('vulyk.app')

        self._leaderboard_manager = \
            self._leaderboard_manager or LeaderBoardManager(self.type_name,
                                                            self.answer_model,
                                                            User)
        self._work_session_manager = \
            self._work_session_manager or WorkSessionManager(WorkSession)

        assert issubclass(self.task_model, AbstractTask), \
            'You should define task_model property'
        assert issubclass(self.answer_model, AbstractAnswer), \
            'You should define answer_model property'

        assert isinstance(self._work_session_manager, WorkSessionManager), \
            'You should define _work_session_manager property'
        assert isinstance(self._leaderboard_manager, LeaderBoardManager), \
            'You should define _leaderboard_manager property'

        assert self.type_name, 'You should define type_name (underscore)'
        assert self.template, 'You should define template'
        assert isinstance(self._task_type_meta, dict), \
            'Batch meta must of dict type'

    @property
    def name(self):
        """
        Human-readable name of the plugin.

        :return: Name of the task type.
        :rtype: str
        """
        return self._name if len(self._name) > 0 else self.type_name

    @property
    def task_type_meta(self):
        """
        Dict with task type metadata (freeform dict)

        :return: project specific metadata
         :rtype: dict
        """
        return self._task_type_meta

    @property
    def description(self):
        """
        Explicit description of the plugin.

        :return: Plugin description.
        :rtype: str
        """
        return self._description if len(self._description) > 0 else ''

    @property
    def work_session_manager(self) -> WorkSessionManager:
        """
        Returns current instance of WorkSessionManager used in the task type.

        :return: Active WorkSessionManager instance.
        :rtype: WorkSessionManager
        """
        return self._work_session_manager

    def import_tasks(self, tasks, batch):
        """Imports tasks from an iterable over dicts
        io is left out of scope here.

        :param tasks: An iterable over dicts
        :type tasks: tuple[dict]
        :param batch: Batch ID (optional)
        :type batch: str

        :raise: TaskImportError
        """
        errors = (AttributeError, TypeError, ValidationError, OperationError,
                  AssertionError)
        bulk = []

        try:
            for task in tasks:
                assert isinstance(task, dict)

                bulk.append(self.task_model(
                    id=sha1(json.dumps(task).encode('utf8')).hexdigest()[:20],
                    batch=batch,
                    task_type=self.type_name,
                    task_data=task))

            self.task_model.objects.insert(bulk)

            self._logger.debug('Inserted %s tasks in batch %s for plugin <%s>',
                               len(bulk), batch, self.name)
        except errors as e:
            raise TaskImportError('Can\'t load task: {}'.format(e))

    def export_reports(self, batch, closed=True, qs=None):
        """Exports results. IO is left out of scope here as well

        :param batch: Certain batch to extract
        :type batch: str
        :param closed: Specify if we need to export only closed tasks reports
        :type closed: bool
        :param qs: Queryset, an optional argument. Default value is QS that
                   exports all tasks with amount of answers > redundancy
        :type qs: QuerySet

        :returns: Generator of lists of dicts with results
        :rtype: __generator[dict]
        """
        if qs is None:
            query = Q()

            if batch != '__all__':
                query &= Q(batch=batch)

            if closed:
                query &= Q(closed=closed)

            qs = self.task_model.objects(query)

        for task in qs:
            yield from map(lambda a: a.as_dict(),
                           self.answer_model.objects(task=task))

    def get_leaders(self):
        """Return sorted list of tuples (user_id, tasks_done)

        :returns: list of tuples (user_id, tasks_done)
        :rtype: list[tuple[bson.ObjectId, int]]
        """
        return self._leaderboard_manager.get_leaders()

    def get_leaderboard(self, limit=10):
        """Find users who contributed the most

        :param limit: number of top users to return
        :type limit: integer

        :returns: List of dicts {user: user_obj, freq: count}
        :rtype: list[dict]
        """
        return self._leaderboard_manager.get_leaderboard(limit)

    def get_next(self, user):
        """
        Finds given user a new task and starts new WorkSession

        :param user: an instance of User model
        :type user: vulyk.models.user.User

        :returns: Prepared dictionary of model, or empty dictionary
        :rtype: dict
        """
        task = self._get_next_task(user)

        if task is not None:
            # Not sure if we should do that here on GET requests
            self._work_session_manager.start_work_session(task, user.id)

            self._logger.debug('Assigned task %s to user %s', task.id, user.id)

            return task.as_dict()
        else:
            self._logger.debug('No suitable task found for  user %s', user.id)

            return {}

    def _get_next_task(self, user):
        """
        Finds given user a new task

        :param user: an instance of User model
        :type user: models.User

        :returns: Model instance or None
        :rtype: AbstractTask
        """
        rs = None
        base_q = Q(task_type=self.type_name) \
            & Q(users_processed__nin=[user]) \
            & Q(closed__ne=True)

        for batch in Batch.objects.order_by('id'):
            if batch.tasks_count == batch.tasks_processed:
                continue

            rs = self.task_model.objects(
                base_q & Q(users_skipped__nin=[user]) & Q(batch=batch.id))

            if rs.count() == 0:
                del rs
                rs = self.task_model.objects(base_q & Q(batch=batch.id))

            if rs.count() > 0:
                break
        else:
            # Now searching w/o batch restriction
            rs = self.task_model.objects(
                base_q & Q(users_skipped__nin=[user]))

            if rs.count() == 0:
                del rs
                rs = self.task_model.objects(base_q)

        if rs:
            _id = random.choice(rs.distinct('id') or [])

            try:
                return rs.get(id=_id)
            except self.task_model.DoesNotExist:
                self._logger.error(
                    'DoesNotExist when trying to fetch task {}'.format(_id))

                return None
        else:
            return None

    def record_activity(self, user_id, task_id, seconds):
        """
        Increases the counter of activity for current user in given task.

        :param task_id: Current task
        :type task_id: str
        :param user_id: ID of user, who gets new task
        :type user_id: bytes, str, bson.ObjectId
        :param seconds: User was active for
        :type seconds: int

        :raises: TaskSkipError, TaskNotFoundError
        """
        try:
            task = self.task_model.objects.get(id=task_id,
                                               task_type=self.type_name)

            self._work_session_manager.record_activity(task, user_id, seconds)

            self._logger.debug('Recording %s seconds of activity of user %s '
                               'on task %s', seconds, user_id, task_id)
        except self.task_model.DoesNotExist:
            raise TaskNotFoundError()

    def skip_task(self, task_id, user):
        """
        Marks given task as a skipped by a given user
        Assumes that user is eligible for this kind of tasks

        :param task_id: Given task ID
        :type task_id: basestring
        :param user: an instance of User model who provided an answer
        :type user: models.User

        :raises: TaskSkipError, TaskNotFoundError
        """
        try:
            task = self.task_model.objects.get(
                id=task_id,
                task_type=self.type_name)

            task.update(add_to_set__users_skipped=user)
            self._work_session_manager.delete_work_session(task, user.id)

            self._logger.debug('User %s skipped the task %s', user.id, task_id)
        except self.task_model.DoesNotExist:
            raise TaskNotFoundError()
        except OperationError as err:
            raise TaskSkipError('Can not skip the task: {0}.'.format(err))

    def on_task_done(self, user, task_id, result):
        """
        Saves user's answers for a given task.
        Assumes that user is eligible for this kind of tasks.

        :param task_id: Given task ID
        :type task_id: str
        :param user: an instance of User model who provided an answer
        :type user: vulyk.models.user.User
        :param result: Task solving result
        :type result: dict

        :raises: TaskSaveError - in case of general problems
        :raises: TaskValidationError - in case of validation problems
        """

        answer = None
        try:
            task = self.task_model.objects.get(
                id=task_id,
                task_type=self.type_name)
        except self.task_model.DoesNotExist:
            raise TaskNotFoundError('Task with ID {id} not found while '
                                    'trying to save an answer from {user!r}.'
                                    .format(id=task_id, user=user))

        try:
            answer = self.answer_model.objects.create(
                task=task,
                created_by=user,
                created_at=datetime.now(),
                task_type=self.type_name,
                result=result)

            # update task
            closed = self._update_task_on_answer(task, answer, user)
            # update user
            user.update(inc__processed=1)
            # update stats record
            self._work_session_manager.end_work_session(task, user.id, answer)

            self._logger.debug('User %s has done task %s', user.id, task_id)

            if closed and task.batch is not None:
                batch_id = task.batch.id
                Batch.objects(id=batch_id).update_one(inc__tasks_processed=1)
        except NotUniqueError:
            raise TaskValidationError('Attempt to save over the existing '
                                      'answer for task {id} by user {user!r}'
                                      .format(id=task_id, user=user))
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

        :rtype: bool
        """
        task.users_count += 1
        task.users_processed.append(user)

        closed = self._is_ready_for_autoclose(task, answer) \
            or (task.users_count >= self.redundancy)

        if closed:
            task.closed = closed

        task.save()

        return closed

    def to_dict(self):
        """
        Prepare simplified dict that contains basic info about the task type.

        :return: distilled dict with basic info
        :rtype: dict
        """
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type_name,
            'tasks': self.task_model.objects.count()
        }
