# -*- coding: utf-8 -*-
"""
The factory of achievements. Classes below allow us to query data source we use
as a source of truth.
"""
from bson import ObjectId
from datetime import date, timedelta
from collections import namedtuple

from mongoengine.queryset.base import BaseQuerySet

from .rules import Rule, ProjectRule

__all__ = [
    'RULES',
    'RuleQueryBuilder',
    'MongoRuleQueryBuilder',
    'MongoRuleExecutor'
]


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

    def build_for(self, user_id: ObjectId) -> list:
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

        # we filter out tasks older than given date in these cases:
        # - n tasks in m days
        is_tasks_in_days = rule.days_number > 0 and rule.tasks_number > 0
        # - has been working for m adjacent days/weekends
        is_adjacent = rule.days_number > 0 and rule.is_adjacent

        if is_tasks_in_days or is_adjacent:
            days_ago = timedelta(days=rule.days_number)

            if is_adjacent and rule.is_weekend:
                # multiply by week length
                days_ago *= 7

            then = date.today() - days_ago
            self._filter_first['end_date'] = {'$gt': then}

        # filter by tasks closed on Saturday or Sunday only
        if rule.is_weekend:
            self._projection = {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'},
            }
            # mongoDB aggregation framework takes Sunday as 1 and Saturday as 7
            self._filter_second = {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}

        # count by days with at least one task closed
        count_by_days = rule.days_number > 0 and rule.tasks_number == 0

        if count_by_days:
            if rule.is_weekend:
                self._group = {'_id': {'week': '$week', 'year': '$year'}}
            else:
                self._projection = {
                   'day': {'$day': '$end_date'},
                   'month': {'$month': '$end_date'},
                   'year': {'$year': '$end_date'}
                }
                self._group = {
                    '_id': {'day': '$day', 'month': '$month', 'year': '$year'}
                }

    def build_for(self, user_id: ObjectId) -> list:
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
    @staticmethod
    def achieved(user_id: ObjectId,
                 rule: Rule,
                 collection: BaseQuerySet) -> bool:
        """
        Determines if given user has achieved a new prize.

        :param user_id: Current user ID
        :type user_id: bson.ObjectId
        :param rule: Rule to be applied
        :type rule: Rule
        :param collection: WorkSession querySet
        :type collection: BaseQuerySet

        :return: True if user stats comply to the rule
        :rtype: bool
        """

        # there is no way to get the size of aggregated batch using pymongo
        # except explicit cursor dereferencing.
        query = MongoRuleQueryBuilder(rule).build_for(user_id)

        return sum([1 for _ in collection.aggregate(query)]) >= rule.limit
