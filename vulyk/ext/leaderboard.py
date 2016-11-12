# -*- coding: utf-8 -*-
from collections import defaultdict
from operator import itemgetter

__all__ = [
    'LeaderBoardManager'
]


class LeaderBoardManager:
    def __init__(self, task_type_name, answer_model, user_model):
        self._task_type_name = task_type_name
        self._answer_model = answer_model
        self._user_model = user_model

    def get_leaders(self):
        """Return sorted list of tuples (user_id, tasks_done)

        :returns: list of tuples (user_id, tasks_done)
        :rtype: list[tuple[bson.ObjectId, int]]
        """
        scores = self._answer_model \
            .objects(task_type=self._task_type_name) \
            .item_frequencies('created_by')

        return sorted(scores.items(), key=itemgetter(1), reverse=True)

    def get_leaderboard(self, limit):
        """Find users who contributed the most

        :param limit: number of top users to return
        :type limit: integer

        :returns: List of dicts {user: user_obj, freq: count}
        :rtype: list[dict]
        """
        result = []
        top = defaultdict(list)

        [top[e[1]].append(e) for e in self.get_leaders() if len(top) < limit]

        sorted_top = sorted(top.values(), key=lambda r: r[0][1], reverse=True)

        for i, el in enumerate(sorted_top):
            for v in el:
                result.append({
                    'rank': i + 1,
                    'user': self._user_model.objects.get(id=v[0]),
                    'freq': v[1]})

        return result
