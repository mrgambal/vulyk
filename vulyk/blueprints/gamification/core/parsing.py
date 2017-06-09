# -*- coding: utf-8 -*-
"""
All available parsers, that convert raw representation could be received from
any external source, are and should be kept here.
"""
import ujson as json

from .rules import Rule, ProjectRule


class RuleParsingException(Exception):
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
            rule = Rule(parsee['badge'],
                        parsee['name'],
                        parsee['description'],
                        int(parsee['bonus']),
                        int(parsee['tasks_number']),
                        int(parsee['days_number']),
                        bool(parsee['is_weekend']),
                        bool(parsee['is_adjacent']),
                        json_string)

            if 'task_type' not in parsee:
                return rule
            else:
                return ProjectRule.from_rule(rule,
                                             parsee['task_type'],
                                             json_string)
        except ValueError:
            raise RuleParsingException('Can not parse {}'.format(json_string))
        except KeyError as e:
            raise RuleParsingException('Invalid JSON passed: {}'.format(e))
