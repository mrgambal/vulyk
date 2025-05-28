# -*- coding: utf-8 -*-
from collections import defaultdict
from operator import itemgetter
from typing import TYPE_CHECKING

from bson import ObjectId

if TYPE_CHECKING:
    from vulyk.models.tasks import AbstractAnswer
    from vulyk.models.user import User


__all__ = ["LeaderBoardManager"]


class LeaderBoardManager:
    """
    Manager for leaderboard operations for a specific task type in Vulyk.

    Provides methods to retrieve user rankings based on the number of tasks completed.
    """

    def __init__(self, task_type_name: str, answer_model: type["AbstractAnswer"], user_model: type["User"]) -> None:
        """
        Initialize the LeaderBoardManager.

        :param task_type_name: Name of the current task type.
        :param answer_model: Model class representing answers for the task type.
        :param user_model: Model class representing users.
        """
        self._task_type_name = task_type_name
        self._answer_model = answer_model
        self._user_model = user_model

    def get_leaders(self) -> list[tuple[ObjectId, int]]:
        """
        Return a sorted list of tuples (user_id, tasks_done) for the current task type.

        :returns: List of tuples (user_id, tasks_done), sorted in descending order by tasks_done.
        """
        scores = self._answer_model.objects(task_type=self._task_type_name).item_frequencies("created_by")

        return sorted(scores.items(), key=itemgetter(1), reverse=True)

    def get_leaderboard(self, limit: int) -> list[dict[str, "User | int"]]:
        """
        Find the top users who contributed the most to the current task type.

        :param limit: Number of top users to return.
        :returns: List of dicts {rank: rank, user: user_obj, freq: count}, where rank is 1-based.
        """
        result = []
        top: dict[str, list[tuple[ObjectId, int]]] = defaultdict(list)

        _ = [top[e[1]].append(e) for e in self.get_leaders() if len(top) < limit]  # type: ignore[func-returns-value,index]

        sorted_top = sorted(top.values(), key=lambda r: r[0][1], reverse=True)

        for i, el in enumerate(sorted_top):
            for v in el:
                result.append({"rank": i + 1, "user": self._user_model.objects.get(id=v[0]), "freq": v[1]})

        return result
