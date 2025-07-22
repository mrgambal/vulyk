# -*- coding: utf-8 -*-
"""
Parsers for converting raw data from external sources into structured objects.

All parser implementations should be kept in this module.
"""

import orjson as json

from .rules import ProjectRule, Rule


class RuleParsingException(Exception):
    """
    Basic exception for all types of rule parsing errors
    """


class RuleParser:
    """
    Just a stub in case if we want to extend parsing sources.
    """

    __slots__ = []


class JsonRuleParser(RuleParser):
    """
    Basic JSON parser.
    """

    __slots__ = []

    @staticmethod
    def parse(json_string: str) -> Rule | ProjectRule:
        """
        Parse JSON-encoded string to an actual rule object.

        :param json_string: JSON containing achievement data
        :return: A fully parsed rule object
        :raises RuleParsingException: When parsing fails due to invalid input
        """
        try:
            parsee = json.loads(json_string)
            name = parsee["name"]
            task_type_name = parsee.get("task_type_name", "")
            hash_id = str(hash("{}{}".format(name, task_type_name)))

            rule = Rule(
                rule_id=hash_id,
                badge=parsee["badge"],
                name=name,
                description=parsee["description"],
                bonus=int(parsee["bonus"]),
                tasks_number=int(parsee["tasks_number"]),
                days_number=int(parsee["days_number"]),
                is_weekend=bool(parsee["is_weekend"]),
                is_adjacent=bool(parsee["is_adjacent"]),
            )

            if task_type_name:
                return ProjectRule.from_rule(rule, task_type_name)

            return rule
        except ValueError as e:
            raise RuleParsingException(f"Cannot parse: {json_string}") from e
        except (TypeError, KeyError) as e:
            raise RuleParsingException(f"Invalid JSON structure: {e}") from e
