# -*- coding: utf-8 -*-
from typing import Any, ClassVar

from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import Batch

POINTS_PER_TASK_KEY = "points_per_task"
COINS_PER_TASK_KEY = "coins_per_task"
IMPORTANT_KEY = "is_important"


class AbstractGamifiedTaskType(AbstractTaskType):
    _task_type_meta: ClassVar[dict[str, float | bool]] = {
        POINTS_PER_TASK_KEY: 1.0,
        COINS_PER_TASK_KEY: 1.0,
        IMPORTANT_KEY: False,
    }

    def _get_next_open_batch(self) -> Batch | None:
        """
        :return: Next open batch for this task type
        """

        for batch in Batch.objects.filter(task_type=self.type_name, closed__ne=True).order_by("id"):
            if batch.tasks_count == batch.tasks_processed:
                continue

            return batch

        return None

    def to_dict(self) -> dict[str, str | dict[str, Any] | None]:
        """
        Prepare simplified dict that contains basic info about the task type +
        information on next open batch

        :return: distilled dict with basic info
        """

        resp = super(AbstractGamifiedTaskType, self).to_dict()
        batch = self._get_next_open_batch()
        resp["batch_info"] = batch.batch_meta if batch else None

        return resp
