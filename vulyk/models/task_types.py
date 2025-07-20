# -*- coding: utf-8 -*-
"""Defines the core `AbstractTaskType` class, representing a Vulyk task type plugin."""

import logging
import random
from collections.abc import Generator, Sequence
from datetime import datetime, timezone
from hashlib import sha1
from typing import Any, ClassVar, Generic, TypeVar

import orjson as json
from bson import ObjectId
from mongoengine import Q, QuerySet
from mongoengine.errors import InvalidQueryError, LookUpError, NotUniqueError, OperationError, ValidationError

from vulyk.ext.leaderboard import LeaderBoardManager
from vulyk.ext.worksession import WorkSessionManager
from vulyk.models.exc import TaskImportError, TaskNotFoundError, TaskSaveError, TaskSkipError, TaskValidationError
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractAnswer, AbstractTask, Batch
from vulyk.models.user import User

__all__ = ["AbstractTaskType"]

TAbstractTask = TypeVar("TAbstractTask", bound=AbstractTask)
TAbstractAnswer = TypeVar("TAbstractAnswer", bound=AbstractAnswer)


class AbstractTaskType(Generic[TAbstractTask, TAbstractAnswer]):
    """
    Represents a specific type of task within Vulyk (often implemented as a plugin).
    This abstract base class encapsulates the core logic for task management,
    including task retrieval, submission, user assignment, and result aggregation.

    Subclasses should override properties like `task_model`, `answer_model`,
    `type_name`, `template`, etc., and potentially methods like
    `_is_ready_for_autoclose` to customize behavior.

    Uses Generic types `TAbstractTask` and `TAbstractAnswer` to allow subclasses
    to specify their concrete Task and Answer model types.
    """

    # Concrete models used by this task type
    answer_model: type[TAbstractAnswer]  # The specific Answer model class
    task_model: type[TAbstractTask]  # The specific Task model class

    # --- Configuration properties (must be overridden by subclasses) ---
    template: str = ""  # Path to the Jinja2 template for rendering the task interface
    helptext_template: str = ""  # Path to the Jinja2 template for the help/instructions section
    type_name: str = ""  # Unique identifier for the task type (used in DB queries, URLs, etc.)

    # --- Optional configuration properties ---
    redundancy: int = 3  # Default number of answers required before a task is considered closed
    JS_ASSETS: ClassVar[list[str]] = []  # List of JavaScript asset paths required by the task type template
    CSS_ASSETS: ClassVar[list[str]] = []  # List of CSS asset paths required by the task type template

    # --- Display properties (can be overridden) ---
    _name: str = ""  # Human-readable name (defaults to type_name if empty)
    _description: str = ""  # Detailed description of the task type

    # --- Metadata ---
    # Meta information specific to this task type, copied to task batches upon creation.
    _task_type_meta: ClassVar[dict[str, Any]] = {}

    # --- Internal Managers ---
    # These are typically instantiated in __init__ if not provided by a subclass.
    _work_session_manager: WorkSessionManager
    _leaderboard_manager: LeaderBoardManager

    def __init__(self, settings: dict[str, Any]) -> None:
        """
        Initializes the AbstractTaskType instance.

        Ensures that required models and properties are defined and initializes
        internal managers like WorkSessionManager and LeaderBoardManager.

        :param settings: Global application settings dictionary, passed during
                         plugin instantiation. Can be used by subclasses.
        :raises AssertionError: If required attributes like `task_model`,
                                `answer_model`, `type_name`, or `template`
                                are not defined or have incorrect types.
        """
        self._logger = logging.getLogger("vulyk.app")

        assert hasattr(self, "task_model") and issubclass(self.task_model, AbstractTask), (
            "You should define task_model property"
        )
        assert hasattr(self, "answer_model") and issubclass(self.answer_model, AbstractAnswer), (
            "You should define answer_model property"
        )

        if not hasattr(self, "_leaderboard_manager"):
            self._leaderboard_manager = LeaderBoardManager(self.type_name, self.answer_model, User)
        if not hasattr(self, "_work_session_manager"):
            self._work_session_manager = WorkSessionManager(WorkSession)

        assert isinstance(self._work_session_manager, WorkSessionManager), (
            "You should define _work_session_manager property"
        )
        assert isinstance(self._leaderboard_manager, LeaderBoardManager), (
            "You should define _leaderboard_manager property"
        )

        assert self.type_name, "You should define type_name (underscore)"
        assert self.template, "You should define template"
        assert isinstance(self._task_type_meta, dict), "Batch meta must of dict type"

    @property
    def name(self) -> str:
        """
        Returns the human-readable name for this task type.

        Falls back to `type_name` if `_name` is not explicitly set.

        :return: The name of the task type.
        """
        return self._name or self.type_name

    @property
    def task_type_meta(self) -> dict[str, Any]:
        """
        Returns the dictionary containing task type specific metadata.

        This metadata is often copied to associated `Batch` objects.

        :return: Task type specific metadata dictionary.
        """
        return self._task_type_meta

    @property
    def description(self) -> str:
        """
        Returns the description for this task type.

        :return: The task type description string.
        """
        return self._description or ""

    @property
    def work_session_manager(self) -> WorkSessionManager:
        """
        Provides access to the WorkSessionManager instance for this task type.

        :return: The active WorkSessionManager instance.
        """
        return self._work_session_manager

    def import_tasks(self, tasks: Sequence[dict], batch: str | None) -> None:
        """Imports a list of tasks into the database for this task type.

        Handles the creation of task documents from raw dictionary data,
        assigning them a unique ID based on their content hash, and associating
        them with an optional batch ID. Assumes task data is already loaded
        (e.g., from a file or API).

        :param tasks: A list of dictionaries, where each dictionary represents
                      the `task_data` for a single task.
        :param batch: An optional identifier for the batch these tasks belong to.
        :raise TaskImportError: If any task fails validation or database insertion.
        :raise AssertionError: If `tasks` contains non-dict items.
        """
        errors = (AttributeError, TypeError, ValidationError, OperationError, AssertionError)
        bulk = []

        try:
            for task in tasks:
                assert isinstance(task, dict)

                bulk.append(
                    self.task_model(
                        # Generate a unique ID based on the task data content hash
                        id=sha1(json.dumps(task)).hexdigest()[:20],
                        batch=batch,
                        task_type=self.type_name,
                        task_data=task,
                    )
                )

            self.task_model.objects.insert(bulk)

            self._logger.debug("Inserted %s tasks in batch %s for plugin <%s>", len(bulk), batch, self.name)
        except errors as e:
            raise TaskImportError("Can't load task.") from e

    def export_reports(
        self, batch: str, *, closed: bool = True, qs: QuerySet | None = None
    ) -> Generator[list[dict[str, Any]]]:
        """Exports task results (answers) for a given batch or query.

        Retrieves answers associated with tasks matching the specified criteria.
        Assumes results will be handled externally (e.g., written to a file).

        :param batch: The ID of the batch to export results from. Use "__all__"
                      to export from all batches.
        :param closed: If True, export results only for tasks marked as closed.
        :param qs: An optional MongoEngine QuerySet to use for selecting tasks.
                   If None, a default query is constructed based on `batch` and
                   `closed` parameters.
        :yields: Lists of dictionaries, where each inner list contains all
                 answer dictionaries (`answer.as_dict()`) for a single task.
        """
        if qs is None:
            query = Q()

            if batch != "__all__":
                query &= Q(batch=batch)

            if closed:
                query &= Q(closed=closed)

            qs = self.task_model.objects(query)

        for task in qs:
            yield [a.as_dict() for a in self.answer_model.objects(task=task)]

    def get_leaders(self) -> list[tuple[ObjectId, int]]:
        """Retrieves the raw leaderboard data.

        Uses the LeaderBoardManager to get a sorted list of user contributions.

        :returns: A sorted list of tuples: `(user_id, tasks_done_count)`.
        """
        return self._leaderboard_manager.get_leaders()

    def get_leaderboard(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieves the formatted leaderboard with user objects.

        Uses the LeaderBoardManager to get the top contributing users.

        :param limit: The maximum number of top users to return.
        :returns: A list of dictionaries, each containing:
                  `{'user': UserObject, 'freq': tasks_done_count}`.
        """
        return self._leaderboard_manager.get_leaderboard(limit)

    def get_next(self, user: User) -> dict[str, Any]:
        """
        Retrieves the next available task for the given user and starts a work session.

        Calls `_get_next_task` to find a suitable task, then uses the
        WorkSessionManager to record the start of the work session.

        :param user: The User instance requesting a task.
        :returns: A dictionary representation of the assigned task (`task.as_dict()`),
                  or an empty dictionary if no suitable task is found.
        """
        task = self._get_next_task(user)

        if task is not None:
            # TODO: Consider if starting the work session should happen elsewhere
            # (e.g., upon task submission or first activity ping) rather than
            # immediately on GET request for the task.
            self._work_session_manager.start_work_session(task, user.id)
            self._logger.debug("Assigned task %s to user %s", task.id, user.id)

            return task.as_dict()

        self._logger.debug("No suitable task found for  user %s", user.id)

        return {}

    def _get_next_task(self, user: User) -> AbstractTask | None:
        """
        Core logic to find the next available task for a user.

        It prioritizes tasks from open batches, attempting to find tasks the user
        has neither processed nor skipped. If no such task exists in the current
        batch, it checks other open batches. As a fallback, it searches across
        all tasks (including those without a batch) that the user hasn't
        processed or skipped. Finally, it considers any task the user hasn't
        processed, even if previously skipped.

        :param user: The User instance for whom to find a task.
        :returns: An instance of `self.task_model` or `None` if no suitable task
                  is found.
        """
        rs = None
        # Base query: tasks of this type, not closed, and not already processed by the user.
        base_q = Q(task_type=self.type_name) & Q(users_processed__nin=[user]) & Q(closed__ne=True)

        # --- Strategy 1: Prioritize tasks in open batches ---
        for batch in Batch.objects(task_type=self.type_name, closed__ne=True).order_by("id"):
            # Skip batches that are already fully processed
            if batch.tasks_count == batch.tasks_processed:
                continue

            # Try finding a task in this batch that the user hasn't skipped
            rs = self.task_model.objects(base_q & Q(users_skipped__nin=[user]) & Q(batch=batch.id))

            if rs.count() == 0:
                # If none found, try finding *any* task in this batch (even skipped ones)
                del rs  # Avoid potential reuse of the empty queryset
                rs = self.task_model.objects(base_q & Q(batch=batch.id))

            # If a task was found in this batch, stop searching
            if rs.count() > 0:
                break
        else:
            # --- Strategy 2: Fallback - Search tasks without batch restriction ---
            # This block executes if the loop completed without finding a task (no `break`).
            # Try finding a task (any batch or no batch) that the user hasn't skipped
            rs = self.task_model.objects(base_q & Q(users_skipped__nin=[user]))

            if rs.count() == 0:
                # Final attempt: Find *any* task matching base_q, even if skipped.
                del rs
                rs = self.task_model.objects(base_q)

        if rs:
            # Select a random task ID from the potential candidates.
            # `distinct("id")` ensures we don't pick the same task multiple times
            # if the query somehow returned duplicates (shouldn't happen with ID).
            # `or []` handles the case where `distinct` returns None or empty list.
            _id = random.choice(rs.distinct("id") or [])

            try:
                return rs.get(id=_id)
            except self.task_model.DoesNotExist:
                self._logger.error("DoesNotExist when trying to fetch task {}".format(_id))

                return None
        else:
            return None

    def record_activity(self, user_id: str | ObjectId, task_id: str, seconds: int) -> None:
        """
        Records user activity time spent on a specific task.

        Uses the WorkSessionManager to update the time spent by the user on the task.

        :param user_id: The ID (str or ObjectId) of the user performing the activity.
        :param task_id: The ID of the task the user is working on.
        :param seconds: The duration of the activity in seconds.
        :raises TaskNotFoundError: If the specified task_id does not exist.
        """
        try:
            task = self.task_model.objects.get(id=task_id, task_type=self.type_name)

            self._work_session_manager.record_activity(task, user_id, seconds)

            self._logger.debug("Recording %s seconds of activity of user %s on task %s", seconds, user_id, task_id)
        except self.task_model.DoesNotExist as err:
            raise TaskNotFoundError() from err

    def skip_task(self, task_id: str, user: User) -> None:
        """
        Marks a task as skipped by a specific user.

        Adds the user to the `users_skipped` list for the task and removes any
        associated work session record.

        :param task_id: The ID of the task being skipped.
        :param user: The User instance who is skipping the task.
        :raises TaskNotFoundError: If the specified task_id does not exist.
        :raises TaskSkipError: If the database update operation fails.
        """
        try:
            task = self.task_model.objects.get(id=task_id, task_type=self.type_name)

            task.update(add_to_set__users_skipped=user)
            self._work_session_manager.delete_work_session(task, user.id)

            self._logger.debug("User %s skipped the task %s", user.id, task_id)
        except self.task_model.DoesNotExist as err:
            raise TaskNotFoundError() from err
        except OperationError as err:
            raise TaskSkipError("Can not skip the task.") from err

    def on_task_done(self, user: User, task_id: str, result: dict[str, Any]) -> None:
        """
        Handles the submission of a user's answer for a completed task.

        Creates an Answer document, updates the Task document (potentially closing it),
        updates user statistics, and finalizes the work session.

        :param user: The User instance who submitted the answer.
        :param task_id: The ID of the task being answered.
        :param result: A dictionary containing the user's answer data.
        :raises TaskNotFoundError: If the specified task_id does not exist.
        :raises TaskValidationError: If the answer data is invalid, or if the user
                                     has already submitted an answer for this task.
        :raises TaskSaveError: If a database operation fails during saving.
        """

        answer = None
        try:
            task = self.task_model.objects.get(id=task_id, task_type=self.type_name)
        except self.task_model.DoesNotExist as err:
            raise TaskNotFoundError(
                "Task with ID {id} not found while trying to save an answer from {user!r}.".format(
                    id=task_id, user=user
                )
            ) from err

        try:
            answer = self.answer_model.objects.create(
                task=task,
                created_by=user,
                created_at=datetime.now(tz=timezone.utc),
                task_type=self.type_name,
                result=result,
            )

            # update task
            closed = self._update_task_on_answer(task, answer, user)
            # update user
            user.update(inc__processed=1)
            # update stats record
            self._work_session_manager.end_work_session(task, user.id, answer)

            self._logger.debug("User %s has done task %s", user.id, task_id)

            if closed and task.batch is not None:
                Batch.task_done_in(batch_id=task.batch.id)
        except NotUniqueError as err:
            raise TaskValidationError(
                "Attempt to save over the existing answer for task {id} by user {user!r}".format(id=task_id, user=user)
            ) from err
        except ValidationError as err:
            raise TaskValidationError() from err
        except (OperationError, LookUpError, InvalidQueryError) as err:
            raise TaskSaveError() from err

    def _is_ready_for_autoclose(self, task: AbstractTask, answer: AbstractAnswer) -> bool:
        """
        Determines if a task can be automatically closed based on the latest answer.

        This method provides a hook for implementing custom task closing logic
        (e.g., based on answer consensus or specific answer content) before
        reaching the standard `redundancy` count. The default implementation
        always returns False.

        Subclasses should override this method to implement specific auto-closing rules.

        :param task: The Task instance being evaluated.
        :param answer: The newly submitted Answer instance.
        :returns: True if the task should be closed based on this answer,
                  False otherwise.
        """
        return False

    def _update_task_on_answer(self, task: AbstractTask, answer: AbstractAnswer, user: User) -> bool:
        """
        Updates the task state after a new answer is submitted.

        Increments the task's answer count (`users_count`), adds the user to
        `users_processed`, and determines if the task should be closed based on
        either the `_is_ready_for_autoclose` logic or reaching the required
        `redundancy` level. Performs an atomic update on the task document.

        Handles a potential race condition where the task might be closed by
        another process between reading and updating.

        :param task: The Task instance to update.
        :param answer: The newly created Answer instance.
        :param user: The User instance who provided the answer.
        :return: True if the task was successfully marked as closed by this operation,
                 False otherwise.
        """
        users_count = task.users_count + 1
        update_q = {"inc__users_count": 1, "add_to_set__users_processed": user}

        # Determine if the task should be closed
        closed = self._is_ready_for_autoclose(task, answer) or (users_count >= self.redundancy)

        if closed:
            update_q["set__closed"] = closed

        num_changed: int = self.task_model.objects(id=task.id, closed=False).update_one(**update_q)

        # Handle race condition: If we intended to close the task (`closed` is True)
        # but the update didn't change anything (`num_changed == 0`), it means
        # another process likely closed the task already. We still need to
        # apply the other updates (inc__users_count, add_to_set__users_processed).
        if closed and num_changed == 0:
            # Task was already closed, don't try to set 'closed' again.
            update_q.pop("set__closed", None)
            closed = False  # Reflect that *this* operation didn't close it.

            # Apply the remaining updates (user count, processed list)
            # This update doesn't need the `closed=False` condition as the task is already closed.
            self.task_model.objects(id=task.id).update_one(**update_q)

        return closed

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a dictionary summarizing the state of this task type.

        Provides key information like name, description, type identifier, and
        task counts (total, open, closed). Useful for displaying task type
        information in UIs or APIs.

        :return: A dictionary containing summary information about the task type.
        """

        closed_tasks: int = self.task_model.objects(closed=True).count()
        tasks: int = self.task_model.objects().count()
        open_tasks: int = tasks - closed_tasks

        return {
            "name": self.name,
            "description": self.description,
            "type": self.type_name,
            "tasks": tasks,
            "open_tasks": open_tasks,
            "closed_tasks": closed_tasks,
            "has_tasks": open_tasks > 0,
        }
