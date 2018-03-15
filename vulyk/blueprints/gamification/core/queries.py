# -*- coding: utf-8 -*-
"""
The factory of achievements. Classes below allow us to query data source we use
as a source of truth.
"""
from datetime import date, datetime, timedelta
from collections import namedtuple

from bson import ObjectId

from mongoengine.queryset.base import BaseQuerySet

from .rules import Rule, ProjectRule

__all__ = [
    'MongoRuleExecutor',
    'MongoRuleQueryBuilder',
    'RuleQueryBuilder'
]


class RuleQueryBuilder:
    """
    Abstract query builder. Takes an instance of Rule-type and converts its
    properties into fully fledged queries to a data source.
    """

    def __init__(self) -> None:
        self._filter_first = {}  # type: dict
        self._projection = {}  # type: dict
        self._filter_second = {}  # type: dict
        self._group = {}  # type: dict

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
    __slots__ = []

    _Pair = namedtuple('Pair', ['key', 'clause'])

    def __init__(self, rule: Rule) -> None:
        """
        :param rule: Actual rule to be calculated.
        :type rule: Rule
        """
        super().__init__()

        self._filter_first['answer'] = {'$exists': True}
        if isinstance(rule, ProjectRule):
            self._filter_first['taskType'] = rule.task_type_name

        # we filter out tasks older than given date in these cases:
        # - n tasks in m days
        is_tasks_in_days = (rule.days_number or 0) > 0 and (rule.tasks_number or 0) > 0
        # - has been working for m adjacent days/weekends
        is_adjacent = (rule.days_number or 0) > 0 and rule.is_adjacent

        if is_tasks_in_days or is_adjacent:
            days_ago = timedelta(days=rule.days_number)

            if is_adjacent and rule.is_weekend:
                # multiply by week length
                days_ago *= 7

            then = datetime.combine(date.today() - days_ago,
                                    datetime.min.time())

            self._filter_first['end_time'] = {'$gt': then}

        # filter by tasks closed on Saturday or Sunday only
        if rule.is_weekend:
            self._projection = {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'},
            }
            # mongoDB aggregation framework takes Sunday as 1 and Saturday as 7
            self._filter_second = {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}

        # count by days with at least one task closed
        count_by_days = (rule.days_number or 0) > 0 and (rule.tasks_number or 0) == 0

        if count_by_days:
            if rule.is_weekend:
                self._group = {'_id': {'week': '$week', 'year': '$year'}}
            else:
                self._projection = {
                    'day': {'$dayOfMonth': '$end_time'},
                    'month': {'$month': '$end_time'},
                    'year': {'$year': '$end_time'}
                }
                self._group = {
                    '_id': {
                        'day': '$day',
                        'month': '$month',
                        'year': '$year'}
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

        for statement in [
            self._Pair(key='$project', clause=self._projection),
            self._Pair(key='$match', clause=self._filter_second),
            self._Pair(key='$group', clause=self._group)
        ]:
            if bool(statement.clause):
                result.append({statement.key: statement.clause})

        return result


class MongoRuleExecutor:
    """
    Simple query runner that uses pymongo's BaseQuerySet instance to aggregate
    user's stats.
    """
    __slots__ = []

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

        return sum(1 for _ in collection.aggregate(*query)) >= rule.limit
