# -*- coding: utf-8 -*-
from datetime import datetime
import logging

from flask_mongoengine import Document
from mongoengine.errors import OperationError

from vulyk.models.exc import WorkSessionLookUpError, WorkSessionUpdateError

__all__ = [
    'WorkSessionManager'
]


class WorkSessionManager:
    """
    This class is responsible for accounting of work-sessions.
    Every time we give a task to user, a new session record is being created.
    If user skips the task, we mark it as skipped and delete the session.
    When user finishes the task, we close the session having added the
    timestamp of the event.
    Thus we're able to perform any kind of data mining and stats counting using
    the data later.

    Could be overridden in plugins.
    """

    def __init__(self, work_session_model):
        """
        Constructor.

        :param work_session_model: Underlying mongoDB Document subclass.
        :type work_session_model: type
        """
        assert issubclass(work_session_model, Document), \
            'You should define working session model properly'

        self._logger = logging.getLogger('vulyk.app')

        self.work_session = work_session_model

    def start_work_session(self, task, user_id):
        """
        Starts new WorkSession for given user.
        By default we use `datetime.now` in the underlying model to save in
        `start_time` field.

        A user should finish a certain task only once, that's why we perform
        an upsert below.

        :param task: Given task
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of user, who gets new task
        :type user_id: bson.ObjectId

        :raises:
            WorkSessionUpdateError -- can not start a session
        """
        try:
            existing = self.work_session \
                .objects(user=user_id,
                         task=task,
                         task_type=task.task_type) \
                .modify(upsert=True,
                        set__start_time=datetime.now(),
                        set__activity=0)

            if existing is not None:
                self._logger.debug(
                    'Overwriting existing unfinished session for user %s and '
                    'task %s.', user_id, task.id)
        except OperationError as err:
            msg = 'Can not create a session: {}.'.format(err)
            raise WorkSessionUpdateError(msg)

    def record_activity(self, task, user_id, seconds):
        """
        Update an activity counter.
        The intention is to find out how much time was actually spent
        working on the task, excluding sexting, brewing coffee and jogging.

        :param task: The task the session belongs to.
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of current user
        :type user_id: bson.ObjectId
        :param seconds: User was active for
        :type seconds: int

        :raises:
            WorkSessionLookUpError -- session is not found;
            WorkSessionUpdateError -- can not update the session
        """
        try:
            session = self.work_session \
                .objects.get(user=user_id,
                             task=task)
            duration = datetime.now() - session.start_time

            if duration.total_seconds() > seconds + session.activity > 0:
                session.activity += seconds
                session.save()

                self._logger.debug(
                    'Added %s seconds of activities for user %s and task %s.',
                    user_id, task.id)
            else:
                msg = 'Can not update the session {} for user {}. Value: {}.' \
                    .format(session.id, user_id, seconds)
                raise WorkSessionUpdateError(msg)
        except self.work_session.DoesNotExist:
            msg = 'Did not found a session for user {} and task {}.'.format(
                user_id, task.id)
            raise WorkSessionLookUpError(msg)

    def end_work_session(self, task, user_id, answer):
        """
        Ends given WorkSession for given user.
        This is the route for correctly finished tasks: given session to be
        marked as closed and a timestamp of the event to be saved.

        :param task: Given task
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of user, who finishes a task
        :type user_id: bson.ObjectId
        :param answer: Given answer
        :type answer: vulyk.models.tasks.AbstractAnswer

        :raises:
            WorkSessionLookUpError -- session is not found;
            WorkSessionUpdateError -- can not close the session
        """
        # TODO: store id of active session in cookies or elsewhere
        try:
            rs = self.work_session \
                .objects(user=user_id, task=task) \
                .order_by('-start_time')

            if rs.count() > 0:
                rs.first().update(
                    set__end_time=datetime.now(),
                    set__answer=answer)
            else:
                msg = 'No session was found for {0}'.format(answer)

                raise WorkSessionLookUpError(msg)
        except OperationError as e:
            raise WorkSessionUpdateError(e)

    def delete_work_session(self, task, user_id):
        """
        Deletes current WorkSession if skipped.

        :param task: Given task
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of user, who skips a task
        :type user_id: bson.ObjectId

        :raises:
            WorkSessionLookUpError -- session is not found;
            WorkSessionUpdateError -- can not delete the session
        """
        try:
            rs = self.work_session \
                .objects(user=user_id, task=task) \
                .order_by('-start_time')

            if rs.count() > 0:
                rs.first().delete()
            else:
                msg = 'No session was found for {0} & {1}'.format(
                    user_id, task.id)

                raise WorkSessionLookUpError(msg)
        except OperationError as e:
            raise WorkSessionUpdateError(e)
