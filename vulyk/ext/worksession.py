# -*- coding: utf-8 -*-
from datetime import datetime

from flask_mongoengine import Document

from vulyk.models.exc import WorkSessionLookUpError

__all__ = [
    'WorkSessionManager'
]


class WorkSessionManager:
    """
    This class is responsible for accounting of work-sessions.
    Every time we give a task to user, a new session record is being created.
    If user skips the task, we mark it as skipped and delete the session.
    When user finishes the task, we close the session having added the timestamp
    of the event.
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

        self.work_session = work_session_model

    def start_work_session(self, task, user_id):
        """
        Starts new WorkSession for given user.
        By default we use `datetime.now` in the underlying model to save in
        `start_time` field.

        :param task: Given task
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of user, who gets new task
        :type user_id: bytes, str, bson.ObjectId
        """
        self.work_session.objects.create(user=user_id, task=task)

    def end_work_session(self, task, user_id, answer):
        """
        Ends given WorkSession for given user.
        This is the route for correctly finished tasks: given session to be
        marked as closed and a timestamp of the event to be saved.

        :param task: Given task
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of user, who finishes a task
        :type user_id: bytes, str, bson.ObjectId
        :param answer: Given answer
        :type answer: vulyk.models.tasks.AbstractAnswer

        :raises: vulyk.models.exc.WorkSessionLookUpError - if session was not
         found
        """
        # TODO: store id of active session in cookies or elsewhere
        rs = self.work_session \
            .objects(user=user_id, task=task) \
            .order_by('-start_time')

        if rs.count() > 0:
            rs.first().update(
                set__end_time=datetime.now(),
                set__answer=answer,
                set__corrections=answer.corrections)
        else:
            msg = 'No session was found for {0}'.format(answer)

            raise WorkSessionLookUpError(msg)

    def delete_work_session(self, task, user_id):
        """
        Deletes current WorkSession if skipped.

        :param task: Given task
        :type task: vulyk.models.tasks.AbstractTask
        :param user_id: ID of user, who skips a task
        :type user_id: bytes, str, bson.ObjectId

        :raises: vulyk.models.exc.WorkSessionLookUpError - if session was not
         found
        """
        rs = self.work_session \
            .objects(user=user_id, task=task) \
            .order_by('-start_time')

        if rs.count() > 0:
            rs.first().delete()
        else:
            msg = 'No session was found for {0} & {1}'.format(
                user_id, task.id)

            raise WorkSessionLookUpError(msg)
