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
    def __init__(self, task_type_name: str, answer_model: type["AbstractAnswer"], user_model: type["User"]) -> None:
        """
        :param task_type_name: Current task type name.
        :param answer_model: Current answer model.
        :param user_model: Active user model.
        """
        self._task_type_name = task_type_name
        self._answer_model = answer_model
        self._user_model = user_model

    def get_leaders(self) -> list[tuple[ObjectId, int]]:
        """Return sorted list of tuples (user_id, tasks_done).

        :returns: list of tuples (user_id, tasks_done).
        """
        scores = self._answer_model.objects(task_type=self._task_type_name).item_frequencies("created_by")

        return sorted(scores.items(), key=itemgetter(1), reverse=True)

    def get_leaderboard(self, limit: int) -> list[dict[str, "User | int"]]:
        """Find users who contributed the most.

        :param limit: number of top users to return.

        :returns: list of dicts {user: user_obj, freq: count}
        """
        result = []
        top: dict[str, list[tuple[ObjectId, int]]] = defaultdict(list)

        _ = [top[e[1]].append(e) for e in self.get_leaders() if len(top) < limit]  # type: ignore[]

        sorted_top = sorted(top.values(), key=lambda r: r[0][1], reverse=True)

        for i, el in enumerate(sorted_top):
            for v in el:
                result.append({"rank": i + 1, "user": self._user_model.objects.get(id=v[0]), "freq": v[1]})

        return result
