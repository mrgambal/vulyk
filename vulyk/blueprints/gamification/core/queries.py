# -*- coding: utf-8 -*-
"""
The factory of achievements. Classes below allow us to query data source we use
as a source of truth.
"""
from bson import ObjectId
from datetime import date, timedelta
from collections import namedtuple

from .rules import Rule, ProjectRule

__all__ = [
    'RULES',
    'RuleQueryBuilder',
    'MongoRuleQueryBuilder'
]

RULES = []


class RuleQueryBuilder:
    """
    Abstract query builder. Takes an instance of Rule-type and converts its
    properties into fully fledged queries to a data source.
    """

    def __init__(self, rule: Rule) -> None:
        """
        :param rule: Actual rule to be calculated.
        :type rule: Rule
        """

        self._filter_first = {}
        self._projection = {}
        self._filter_second = {}
        self._group = {}

    def build(self, user_id: ObjectId) -> list:
        """
        Prepares a pipeline of actions to be passed to data source.

        :param user_id: Current user ID
        :type user_id: bson.ObjectId

        :returns: List of actions to be done.
        :rtype: list[dict]
        """
        raise NotImplementedError()


class MongoRuleQueryBuilder(RuleQueryBuilder):
    """
    Implementation of RuleQueryBuilder, bound to MongoDB.
    """
    _Pair = namedtuple('Pair', ['key', 'clause'])

    def __init__(self, rule: Rule) -> None:
        """
        :param rule: Actual rule to be calculated.
        :type rule: Rule
        """
        super().__init__(rule)

        if isinstance(rule, ProjectRule):
            self._filter_first['task_type'] = rule.task_type_name

        # you closed n tasks in m days
        if rule.days_number > 0 and rule.tasks_number > 0:
            then = date.today() - timedelta(days=rule.days_number)
            self._filter_first['end_date'] = {'$gt': then}

        # you closed n tasks on weekends
        if rule.is_weekend and rule.tasks_number > 0:
            self._projection = {'dayOfWeek': {'$dayOfWeek': '$end_date'}}
            # mongoDB aggregation framework takes Sunday as 1 and Saturday as 7
            self._filter_second = {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}

    def build(self, user_id: ObjectId) -> list:
        """
        Prepares a pipeline of actions to be passed to MongoDB Aggregation
        Framework.

        :param user_id: Current user ID
        :type user_id: bson.ObjectId

        :returns: List of actions to be done within the aggregation.
        :rtype: list[dict]
        """
        filter_first = self._filter_first.copy()
        filter_first['user'] = user_id

        result = [{'$match': filter_first}]

        [result.append({statement.key: statement.clause}) for statement in [
            self._Pair(key='$project', clause=self._projection),
            self._Pair(key='$match', clause=self._filter_second),
            self._Pair(key='$group', clause=self._group)
        ] if bool(statement.clause)]

        return result


class MongoRuleExecutor:
    def __init__(self, rule: Rule) -> None:
        """
        :param rule:
        :type rule: Rule
        """
