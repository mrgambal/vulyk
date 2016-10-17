# -*-coding:utf-8-*-
from datetime import datetime

from flask_mongoengine import Document

from vulyk.models.exc import WorkSessionLookUpError


class WorksessionManager:
    def __init__(self, work_session_model):
        assert issubclass(work_session_model, Document), \
            'You should define working session model properly'

        self.work_session = work_session_model

    def start_work_session(self, task, user_id):
        """
        Starts new WorkSession

        :param task: Given task
        :type task: AbstractTask
        :param user_id: ID of user, who gets new task
        :type user_id: bytes | str | bson.ObjectId
        """
        self.work_session.objects.create(user=user_id, task=task)

    def end_work_session(self, task, user_id, answer):
        """
        Ends current WorkSession

        :param task: Given task
        :type task: AbstractTask
        :param user_id: ID of user, who finishes a task
        :type user_id: bytes | str | bson.ObjectId
        :param answer: Given answer
        :type answer: AbstractAnswer

        :raises: WorkSessionLookUpError - if session was not found
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
        Deletes current WorkSession if skipped

        :param task: Given task
        :type task: AbstractTask
        :param user_id: ID of user, who skips a task
        :type user_id: bytes | str | bson.ObjectId

        :raises: WorkSessionLookUpError - if session was not found
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
