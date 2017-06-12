# -*- coding: utf-8 -*-
import ujson as json

from vulyk.blueprints.gamification.core.parsing import (
    JsonRuleParser,
    RuleParsingException)
from vulyk.blueprints.gamification.core.rules import (
    Rule,
    RuleValidationException,
    ProjectRule)

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
        adjacent = False
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
            id=hash(string),
            badge=image,
            name=name,
            description=descr,
            bonus=bonus,
            tasks_number=tasks,
            days_number=days,
            is_weekend=weekend,
            is_adjacent=adjacent)

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
        adjacent = False
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
        rule = ProjectRule(id=hash(string),
                           task_type_name=project,
                           badge=image,
                           name=name,
                           description=descr,
                           bonus=bonus,
                           tasks_number=tasks,
                           days_number=days,
                           is_weekend=weekend,
                           is_adjacent=adjacent)

        self.assertEqual(rule, JsonRuleParser.parse(string))

    def test_parse_limits_tasks(self):
        image = 'base64 image'
        name = 'achvm1'
        descr = 'the very best acvmnt'
        bonus = 100
        tasks = 20
        days = 21
        weekend = True
        adjacent = False
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
            id=hash(string),
            badge=image,
            name=name,
            description=descr,
            bonus=bonus,
            tasks_number=tasks,
            days_number=days,
            is_weekend=weekend,
            is_adjacent=adjacent)

        self.assertEqual(rule.limit, tasks)

    def test_parse_limits_days(self):
        image = 'base64 image'
        name = 'achvm1'
        descr = 'the very best acvmnt'
        bonus = 100
        tasks = 0
        days = 21
        weekend = True
        adjacent = False
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
            id=hash(string),
            badge=image,
            name=name,
            description=descr,
            bonus=bonus,
            tasks_number=tasks,
            days_number=days,
            is_weekend=weekend,
            is_adjacent=adjacent)

        self.assertEqual(rule.limit, days)

    def test_parse_hash(self):
        image = 'base64 image'
        name = 'achvm1'
        descr = 'the very best acvmnt'
        bonus = 100
        tasks = 20
        days = 21
        weekend = True
        adjacent = False
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

        self.assertEqual(hash(JsonRuleParser.parse(string)), hash(string))

    def test_fail_non_json(self):
        string = "<xml></xml>"

        self.assertRaises(RuleParsingException,
                          lambda: JsonRuleParser.parse(string))

    def test_fail_malformed_json(self):
        string = '{"1": , "2": "2"}'

        self.assertRaises(RuleParsingException,
                          lambda: JsonRuleParser.parse(string))

    def test_fail_incomplete_json(self):
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

    def test_fail_adjacent_weekend_tasks(self):
        parsee = {
            'badge': 'base64 image',
            'name': 'achvm1',
            'description': 'the very best acvmnt',
            'bonus': 100,
            'tasks_number': 20,
            'days_number': 7,
            'is_weekend': True,
            'is_adjacent': True
        }
        string = json.dumps(parsee)

        self.assertRaises(RuleValidationException,
                          lambda: JsonRuleParser.parse(string))

    def test_fail_adjacent_days_tasks(self):
        parsee = {
            'badge': 'base64 image',
            'name': 'achvm1',
            'description': 'the very best acvmnt',
            'bonus': 100,
            'tasks_number': 20,
            'days_number': 7,
            'is_weekend': False,
            'is_adjacent': True
        }
        string = json.dumps(parsee)

        self.assertRaises(RuleValidationException,
                          lambda: JsonRuleParser.parse(string))

    def test_fail_zero_adjacent_weekends_tasks(self):
        parsee = {
            'badge': 'base64 image',
            'name': 'achvm1',
            'description': 'the very best acvmnt',
            'bonus': 100,
            'tasks_number': 20,
            'days_number': 0,
            'is_weekend': True,
            'is_adjacent': True
        }
        string = json.dumps(parsee)

        self.assertRaises(RuleValidationException,
                          lambda: JsonRuleParser.parse(string))

    def test_fail_zero_adjacent_days_tasks(self):
        parsee = {
            'badge': 'base64 image',
            'name': 'achvm1',
            'description': 'the very best acvmnt',
            'bonus': 100,
            'tasks_number': 20,
            'days_number': 0,
            'is_weekend': False,
            'is_adjacent': True
        }
        string = json.dumps(parsee)

        self.assertRaises(RuleValidationException,
                          lambda: JsonRuleParser.parse(string))

    def test_fail_zero_days_zero_tasks(self):
        parsee = {
            'badge': 'base64 image',
            'name': 'achvm1',
            'description': 'the very best acvmnt',
            'bonus': 100,
            'tasks_number': 0,
            'days_number': 0,
            'is_weekend': False,
            'is_adjacent': False
        }
        string = json.dumps(parsee)

        self.assertRaises(RuleValidationException,
                          lambda: JsonRuleParser.parse(string))
