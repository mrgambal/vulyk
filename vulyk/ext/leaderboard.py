# -*- coding: utf-8 -*-
from collections import defaultdict
from operator import itemgetter
from typing import Dict, List, Tuple, Union

from bson import ObjectId

from vulyk.models.tasks import AbstractAnswer
from vulyk.models.user import User

__all__ = [
    'LeaderBoardManager'
]


class LeaderBoardManager:
    def __init__(self,
                 task_type_name: str,
                 answer_model: AbstractAnswer,
                 user_model: type) -> None:
        """
        :param task_type_name: Current task type name
        :type task_type_name: str
        :param answer_model: Current answer model
        :type answer_model: AbstractAnswer
        :param user_model: Active user model
        :type user_model: User
        """
        self._task_type_name = task_type_name
        self._answer_model = answer_model
        self._user_model = user_model

    def get_leaders(self) -> List[Tuple[ObjectId, int]]:
        """Return sorted list of tuples (user_id, tasks_done)

        :returns: list of tuples (user_id, tasks_done)
        :rtype: List[Tuple[ObjectId, int]]
        """
        scores = self._answer_model \
            .objects(task_type=self._task_type_name) \
            .item_frequencies('created_by')

        return sorted(scores.items(), key=itemgetter(1), reverse=True)

    def get_leaderboard(self, limit: int) -> List[Dict[str, Union[User, int]]]:
        """Find users who contributed the most

        :param limit: number of top users to return
        :type limit: int

        :returns: List of dicts {user: user_obj, freq: count}
        :rtype: List[Dict[str, Union[User, int]]]
        """
        result = []
        top = defaultdict(list)

        _ = [top[e[1]].append(e) for e in self.get_leaders() if len(top) < limit]

        sorted_top = sorted(top.values(), key=lambda r: r[0][1], reverse=True)

        for i, el in enumerate(sorted_top):
            for v in el:
                result.append({
                    'rank': i + 1,
                    'user': self._user_model.objects.get(id=v[0]),
                    'freq': v[1]})

        return result
