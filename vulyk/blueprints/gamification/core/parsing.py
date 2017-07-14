# -*- coding: utf-8 -*-
"""
All available parsers, that convert raw representation could be received from
any external source, are and should be kept here.
"""
import ujson as json

from .rules import Rule, ProjectRule


class RuleParsingException(Exception):
    """
    Basic exception for all types of rule parsing errors
    """
    pass


class RuleParser:
    """
    Just a stub in case if we want to extend parsing sources.
    """
    pass


class JsonRuleParser(RuleParser):
    """
    Basic JSON parser.
    """
    __slots__ = []

    @staticmethod
    def parse(json_string: str) -> Rule:
        """
        Actually perform parsing from JSON-encoded string to an actual rule.

        :param json_string: JSON dict with all the data about the achievement.
        :type json_string: str

        :returns: Fully parsed rule object.
        :rtype: Rule

        :exception: RuleParsingException
        """
        try:
            parsee = json.loads(json_string)
            name = parsee['name']
            task_type_name = parsee.get('task_type_name', '')
            hash_id = hash('{}{}'.format(name, task_type_name))

            rule = Rule(rule_id=hash_id,
                        badge=parsee['badge'],
                        name=name,
                        description=parsee['description'],
                        bonus=int(parsee['bonus']),
                        tasks_number=int(parsee['tasks_number']),
                        days_number=(parsee['days_number']),
                        is_weekend=bool(parsee['is_weekend']),
                        is_adjacent=bool(parsee['is_adjacent']))

            if task_type_name:
                return ProjectRule.from_rule(rule, task_type_name)
            else:
                return rule
        except ValueError:
            raise RuleParsingException('Can not parse {}'.format(json_string))
        except (TypeError, KeyError) as e:
            raise RuleParsingException('Invalid JSON passed: {}'.format(e))
