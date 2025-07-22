# -*- coding: utf-8 -*-
"""
The factory of achievements. Classes below allow us to query data source we use
as a source of truth.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, NamedTuple

from bson import ObjectId
from mongoengine.queryset.base import BaseQuerySet

from .rules import ProjectRule, Rule

__all__ = ["MongoRuleExecutor", "MongoRuleQueryBuilder", "RuleQueryBuilder"]


class RuleQueryBuilder:
    """
    Abstract query builder converts Rule properties into queries for a data source.
    """

    def __init__(self) -> None:
        self._filter_first: dict[str, Any] = {}
        self._projection: dict[str, Any] = {}
        self._filter_second: dict[str, Any] = {}
        self._group: dict[str, dict[str, str]] = {}

    def build_for(self, user_id: ObjectId) -> list[dict[str, Any]]:
        """
        Prepares a pipeline of actions to be passed to data source.

        :param user_id: Current user ID
        :return: List of actions to be executed
        """
        raise NotImplementedError()


class MongoRuleQueryBuilder(RuleQueryBuilder):
    """
    MongoDB-specific implementation of RuleQueryBuilder.
    """

    __slots__ = []

    _Pair = NamedTuple("Pair", [("key", str), ("clause", dict[str, Any])])

    def __init__(self, rule: Rule) -> None:
        """
        Initialize query builder with the specified rule.

        :param rule: Rule to be calculated
        """
        super().__init__()

        self._filter_first["answer"] = {"$exists": True}

        if isinstance(rule, ProjectRule):
            self._filter_first["taskType"] = rule.task_type_name

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

            then = datetime.combine(datetime.now(timezone.utc).date() - days_ago, datetime.min.time())

            self._filter_first["end_time"] = {"$gt": then}

        # filter by tasks closed on Saturday or Sunday only
        if rule.is_weekend:
            self._projection = {
                "dayOfWeek": {"$dayOfWeek": "$end_time"},
                "year": {"$year": "$end_time"},
                "week": {"$week": "$end_time"},
            }
            # mongoDB aggregation framework takes Sunday as 1 and Saturday as 7
            self._filter_second = {"$or": [{"dayOfWeek": 7}, {"dayOfWeek": 1}]}

        # count by days with at least one task closed
        count_by_days = (rule.days_number or 0) > 0 and (rule.tasks_number or 0) == 0

        if count_by_days:
            if rule.is_weekend:
                self._group = {"_id": {"week": "$week", "year": "$year"}}
            else:
                self._projection = {
                    "day": {"$dayOfMonth": "$end_time"},
                    "month": {"$month": "$end_time"},
                    "year": {"$year": "$end_time"},
                }
                self._group = {"_id": {"day": "$day", "month": "$month", "year": "$year"}}

    def build_for(self, user_id: ObjectId) -> list[dict[str, Any]]:
        """
        Prepares a pipeline of actions for MongoDB Aggregation Framework.

        :param user_id: Current user ID
        :return: List of actions to be executed in the aggregation
        """
        filter_first = self._filter_first.copy()
        filter_first["user"] = user_id

        result = [{"$match": filter_first}]

        for statement in (
            self._Pair(key="$project", clause=self._projection),
            self._Pair(key="$match", clause=self._filter_second),
            self._Pair(key="$group", clause=self._group),
        ):
            if bool(statement.clause):
                result.append({statement.key: statement.clause})

        # Add count operation (MongoDB 3.4+)
        # This needs a type annotation to help the type checker
        count_stage: dict[str, Any] = {"$count": "achieved"}
        result.append(count_stage)

        return result


class MongoRuleExecutor:
    """
    Query executor that uses pymongo's BaseQuerySet to aggregate user statistics.
    """

    __slots__ = []

    @staticmethod
    def achieved(user_id: ObjectId, rule: Rule, collection: BaseQuerySet) -> bool:
        """
        Determines if the user has achieved a new prize.

        :param user_id: Current user ID
        :param rule: Rule to be applied
        :param collection: WorkSession querySet
        :return: True if user statistics comply with the rule
        """
        query = MongoRuleQueryBuilder(rule).build_for(user_id)
        cursor = collection.aggregate(*query)

        try:
            record = next(cursor)
            return record["achieved"] >= rule.limit
        except StopIteration:
            return False
