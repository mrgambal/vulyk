# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timezone
from typing import TypeVar, cast

from bson import ObjectId
from mongoengine.errors import OperationError

from vulyk.models.exc import WorkSessionLookUpError, WorkSessionUpdateError
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractAnswer, AbstractTask
from vulyk.signals import on_task_done

__all__ = ["WorkSessionManager"]


class WorkSessionManager:
    """Manages the lifecycle of user work sessions for tasks.

    This class handles the creation, updating, and deletion of WorkSession
    records associated with users performing tasks. It tracks the start time,
    end time, and user activity duration for each session.

    Key responsibilities:
    - Starting a new session when a task is assigned to a user.
    - Recording user activity time within a session.
    - Ending a session when a task is completed successfully.
    - Deleting a session if a task is skipped.

    The recorded session data can be used for analytics, statistics, and
    monitoring user engagement.

    This class is designed to be potentially overridden or extended by plugins
    to customize work session management behavior.
    """

    TSession = TypeVar("TSession", bound=WorkSession)
    work_session: type[WorkSession]  # Class level type hint for the model

    def __init__(self, work_session_model: type[TSession]) -> None:
        """Constructor.

        :param work_session_model: The MongoEngine Document class for work sessions.
        """
        assert issubclass(work_session_model, WorkSession), "You should define working session model properly"

        self._logger = logging.getLogger("vulyk.app")

        self.work_session = work_session_model

    def start_work_session(self, task: AbstractTask, user_id: ObjectId) -> None:
        """Starts or restarts a WorkSession for a given user and task.

        Creates a new WorkSession record or updates an existing one (upsert)
        to mark the beginning of work on a specific task by a user.
        The `start_time` is recorded using the current UTC time.

        If a session for the same user and task already exists (e.g., was
        interrupted), it will be overwritten with a new start time and reset
        activity counter.

        :param task: The task being started.
        :param user_id: The ID of the user starting the task.

        :raises:
            WorkSessionUpdateError: If the database operation fails.
        """
        try:
            existing = self.work_session.objects(user=user_id, task=task, task_type=task.task_type).modify(
                upsert=True, set__start_time=datetime.now(timezone.utc), set__activity=0
            )

            if existing is not None:
                self._logger.debug("Overwriting existing unfinished session for user %s and task %s.", user_id, task.id)
        except OperationError as err:
            msg = "Can not create a session: {}.".format(err)
            raise WorkSessionUpdateError(msg) from err

    def record_activity(self, task: AbstractTask, user_id: ObjectId, seconds: int) -> None:
        """Records user activity time within a work session.

        Updates the `activity` counter for the ongoing session associated
        with the given user and task. This helps track the actual time spent
        actively working on the task.

        The total recorded activity time cannot exceed the total duration
        since the session started.

        :param task: The task associated with the session.
        :param user_id: The ID of the user whose activity is being recorded.
        :param seconds: The duration of the recent activity in seconds.

        :raises:
            WorkSessionLookUpError: If no matching session is found.
            WorkSessionUpdateError: If the provided activity duration is invalid
                                     or the database update fails.
        """
        try:
            session: WorkSession = self.work_session.objects.get(user=user_id, task=task)
            # Ensure comparison is between offset-aware datetimes if start_time is stored aware
            # If start_time is naive, this comparison might be inaccurate across DST changes.
            # Assuming start_time becomes aware after the start_work_session change.
            now_utc = datetime.now(timezone.utc)
            duration = now_utc - cast(datetime, session.start_time).replace(tzinfo=timezone.utc)

            # Check if adding seconds is valid (non-negative and doesn't exceed total time).
            if seconds >= 0 and duration.total_seconds() >= (seconds + session.activity):
                session.activity += seconds
                session.save()

                self._logger.debug("Added %s seconds of activities for user %s and task %s.", seconds, user_id, task.id)
            else:
                msg = "Can not update the session {} for user {}. Value: {}.".format(session.id, user_id, seconds)
                raise WorkSessionUpdateError(msg)
        except self.work_session.DoesNotExist as err:
            msg = "Did not found a session for user {} and task {}.".format(user_id, task.id)
            raise WorkSessionLookUpError(msg) from err

    def end_work_session(self, task: AbstractTask, user_id: ObjectId, answer: AbstractAnswer) -> None:
        """Ends the most recent WorkSession for a user and task upon completion.

        Finds the latest active session for the specified user and task,
        records the `end_time` using the current UTC time, and associates
        the provided answer with the session. It also triggers the
        `on_task_done` signal.

        :param task: The task that was completed.
        :param user_id: The ID of the user who completed the task.
        :param answer: The answer submitted by the user for the task.

        :raises:
            WorkSessionLookUpError: If no active session is found for the user/task.
            WorkSessionUpdateError: If the database update fails.
        """
        # TODO: store id of active session in cookies or elsewhere
        try:
            rs = self.work_session.objects(user=user_id, task=task).order_by("-start_time")

            if rs.count() > 0:
                rs.first().update(set__end_time=datetime.now(timezone.utc), set__answer=answer)

                on_task_done.send(self, answer=answer)
            else:
                msg = "No session was found for {0}.".format(answer)

                raise WorkSessionLookUpError(msg)
        except OperationError as e:
            raise WorkSessionUpdateError() from e

    def delete_work_session(self, task: AbstractTask, user_id: ObjectId) -> None:
        """Deletes the most recent WorkSession for a user and task, e.g., when skipped.

        Finds and removes the latest session record associated with the given
        user and task. This is typically used when a user decides to skip a
        task they had previously started.

        :param task: The task being skipped or cancelled.
        :param user_id: The ID of the user skipping the task.

        :raises:
            WorkSessionLookUpError: If no active session is found for the user/task.
            WorkSessionUpdateError: If the database deletion fails.
        """
        try:
            rs = self.work_session.objects(user=user_id, task=task).order_by("-start_time")

            if rs.count() > 0:
                rs.first().delete()
            else:
                msg = "No session was found for {0} & {1}.".format(user_id, task.id)

                raise WorkSessionLookUpError(msg)
        except OperationError as e:
            raise WorkSessionUpdateError() from e
