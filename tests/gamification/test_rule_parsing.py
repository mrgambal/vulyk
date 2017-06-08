# -*- coding: utf-8 -*-
import ujson as json

from vulyk.blueprints.gamification.core.parsing import (
    JsonRuleParser,
    RuleParsingException)
from vulyk.blueprints.gamification.core.rules import Rule, ProjectRule

from ..base import BaseTest


class TestJsonRulesParsing(BaseTest):
    def test_parse_ok(self):
        image = 'base64 image'
        name = 'achvm1'
        descr = 'the very best acvmnt'
        bonus = 100
        tasks = 20
        days = 21
        weekend = True
        adjacent = True
        parsee = {
            'badge': image,
            'name': name,
            'description': descr,
            'bonus': bonus,
            'tasks_number': tasks,
            'days_number': days,
            'is_weekend': weekend,
            'is_adjacent': adjacent
        }
        string = json.dumps(parsee)
        rule = Rule(
            image, name, descr, bonus, tasks, days, weekend, adjacent, string)

        self.assertEqual(rule, JsonRuleParser.parse(string))

    def test_parse_project_rule_ok(self):
        project = 'fake_task'
        image = 'base64 image'
        name = 'achvm1'
        descr = 'the very best acvmnt'
        bonus = 100
        tasks = 20
        days = 21
        weekend = True
        adjacent = True
        parsee = {
            'task_type': project,
            'badge': image,
            'name': name,
            'description': descr,
            'bonus': bonus,
            'tasks_number': tasks,
            'days_number': days,
            'is_weekend': weekend,
            'is_adjacent': adjacent
        }
        string = json.dumps(parsee)
        rule = ProjectRule(project, image, name, descr, bonus, tasks, days,
                           weekend, adjacent, string)

        self.assertEqual(rule, JsonRuleParser.parse(string))

    def test_parse_non_json(self):
        string = "<xml></xml>"

        self.assertRaises(RuleParsingException,
                          lambda: JsonRuleParser.parse(string))

    def test_malformed_json(self):
        string = '{"1": , "2": "2"}'

        self.assertRaises(RuleParsingException,
                          lambda: JsonRuleParser.parse(string))

    def test_parse_incomplete_json(self):
        image = 'base64 image'
        # let's omit name
        descr = 'the very best acvmnt'
        bonus = 100
        tasks = 20
        days = 21
        weekend = True
        adjacent = True
        parsee = {
            'badge': image,
            'description': descr,
            'bonus': bonus,
            'tasks_number': tasks,
            'days_number': days,
            'is_weekend': weekend,
            'is_adjacent': adjacent
        }
        string = json.dumps(parsee)

        self.assertRaises(RuleParsingException,
                          lambda: JsonRuleParser.parse(string))
