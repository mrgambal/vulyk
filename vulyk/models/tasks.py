# -*- coding: utf-8 -*-
"""Module contains all models directly related to the main entity - tasks."""

from typing import Any, ClassVar, NamedTuple

from bson import ObjectId
from flask_mongoengine.documents import Document
from mongoengine import (
    CASCADE,
    BooleanField,
    DateTimeField,
    DictField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from vulyk.models.user import User
from vulyk.signals import on_batch_done

__all__ = ["AbstractAnswer", "AbstractTask", "Batch", "BatchUpdateResult"]

BatchUpdateResult = NamedTuple("BatchUpdateResult", [("success", bool), ("closed", bool)])


class Batch(Document):
    """
    Helper category to group tasks.
    """

    id = StringField(max_length=50, primary_key=True)
    task_type = StringField(max_length=50, required=True, db_field="taskType")
    tasks_count = IntField(default=0, required=True, db_field="tasksCount")
    tasks_processed = IntField(default=0, db_field="tasksProcessed")
    closed = BooleanField(default=False, required=False)
    batch_meta = DictField(db_field="batchMeta")

    meta: ClassVar[dict[str, Any]] = {
        "collection": "batches",
        "allow_inheritance": True,
        "indexes": ["task_type", "closed"],
    }

    @classmethod
    def task_done_in(cls, batch_id: str) -> BatchUpdateResult:
        """
        Increment needed values upon a task from the batch is done. In case if
        all tasks are finished – close the batch.

        :param batch_id: Batch ID.

        :return: Aggregate which represents complex effect of the method.
        """
        num_changed = 0
        batch = cls.objects.get(id=batch_id)  # type: Batch
        processed = batch.tasks_processed + 1

        if processed > batch.tasks_count:
            return BatchUpdateResult(success=False, closed=False)

        closed = processed == batch.tasks_count
        update_q = {"inc__tasks_processed": 1}

        if closed:
            update_q["set__closed"] = closed
            num_changed = cls.objects(id=batch.id, closed=False).update(**update_q)

        if num_changed == 0:
            update_q.pop("set__closed", None)
            closed = False

            num_changed = batch.update(**update_q)
        elif closed:
            on_batch_done.send(batch)

        return BatchUpdateResult(success=num_changed > 0, closed=closed)

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return "Batch [{id}] ({processed}/{count})".format(
            id=self.id, processed=self.tasks_processed, count=self.tasks_count
        )


class AbstractTask(Document):
    """
    This is AbstractTask model.
    You need to inherit it in your model.
    """

    id = StringField(max_length=200, default="", primary_key=True)
    task_type = StringField(max_length=50, required=True, db_field="taskType")
    batch = ReferenceField(Batch, reverse_delete_rule=CASCADE)

    users_count = IntField(default=0, db_field="usersCount")
    users_processed = ListField(ReferenceField(User), db_field="usersProcessed")
    users_skipped = ListField(ReferenceField(User), db_field="usersSkipped")

    closed = BooleanField(default=False)
    task_data = DictField(required=True)

    meta: ClassVar[dict[str, Any]] = {
        "collection": "tasks",
        "allow_inheritance": True,
        "indexes": ["task_type", "batch"],
    }

    def as_dict(self) -> dict[str, Any]:
        """
        Converts the model-instance into a safe and lightweight dictionary.

        """
        return {"id": self.id, "closed": self.closed, "data": self.task_data}

    @classmethod
    def ids_in_batch(cls, batch: Batch) -> list[str]:
        """
        Collects IDs of all tasks that belong to certain batch.

        :param batch: Batch instance

        :return: List of IDs
        """
        return cls.objects(batch=batch).distinct("id")

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return str(self)


class AbstractAnswer(Document):
    """
    This is AbstractTask model.
    You need to inherit it in your model
    """

    task = ReferenceField(AbstractTask, reverse_delete_rule=CASCADE)
    created_by = ReferenceField(User, reverse_delete_rule=CASCADE, db_field="createdBy")
    created_at = DateTimeField(db_field="createdAt")
    task_type = StringField(max_length=50, required=True, db_field="taskType")
    # not sure - could be extended
    result = DictField()

    meta: ClassVar[dict[str, Any]] = {
        "collection": "reports",
        "allow_inheritance": True,
        "indexes": ["task", "created_by", "created_at", {"fields": ["created_by", "task"], "unique": True}],
    }

    # TODO: decide, if we need it at all
    @property
    def corrections(self) -> int:
        """
        Returns whole amount of actions/corrections given by user in this
        particular answer.

        :return: Count of corrections in this answer.
        """
        return 1

    @corrections.setter
    def corrections(self, value: int) -> None:
        pass

    @corrections.deleter
    def corrections(self) -> None:
        pass

    @classmethod
    def answers_numbers_by_tasks(cls, task_ids: list[str]) -> dict[ObjectId, int]:
        """
        Groups answers, filtered by tasks they belong to, by user and count
        number of answers for every user.

        :param task_ids: List of tasks IDs.

        :return: Map having user IDs as keys and answers numbers as values.
        """
        return cls.objects(task__in=task_ids).item_frequencies("created_by")

    def as_dict(self) -> dict[str, dict[str, Any]]:
        """
        Converts the model-instance into a safe that will include also task
        and user.

        """
        return {"task": self.task.as_dict(), "answer": self.result, "user": self.created_by.as_dict()}

    def __str__(self) -> str:
        return str(self.pk)

    def __repr__(self) -> str:
        return "Report [{} by {}]".format(self.created_by, self.task)
