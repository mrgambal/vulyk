# -*- coding: utf-8 -*-
"""
test_rule_models
"""

from vulyk.blueprints.gamification.core.rules import ProjectRule, Rule

from ..base import BaseTest


class TestRuleModels(BaseTest):
    BADGE_IMAGE = "data:image/png;base64,"
    RULE_ID = 100
    RULE_NAME = "name"
    RULE_DESCRIPTION = "description"
    TASKS_NUMBER = 20
    DAYS_NUMBER = 5
    IS_WEEKEND = True
    IS_ADJACENT = True
    TASK_TYPE_NAME = "declarations"

    def test_task_rule_to_dict(self):
        rule = Rule(
            badge=self.BADGE_IMAGE,
            name=self.RULE_NAME,
            description=self.RULE_DESCRIPTION,
            bonus=0,
            tasks_number=self.TASKS_NUMBER,
            days_number=self.DAYS_NUMBER,
            is_weekend=self.IS_WEEKEND,
            is_adjacent=False,
            rule_id=self.RULE_ID,
        )
        expected = {
            "id": self.RULE_ID,
            "badge": self.BADGE_IMAGE,
            "name": self.RULE_NAME,
            "description": self.RULE_DESCRIPTION,
            "bonus": 0,
            "tasks_number": self.TASKS_NUMBER,
            "days_number": self.DAYS_NUMBER,
            "is_weekend": self.IS_WEEKEND,
            "is_adjacent": False,
        }

        self.assertDictEqual(expected, rule.to_dict())

    def test_days_rule_to_dict(self):
        rule = Rule(
            badge=self.BADGE_IMAGE,
            name=self.RULE_NAME,
            description=self.RULE_DESCRIPTION,
            bonus=0,
            tasks_number=0,
            days_number=self.DAYS_NUMBER,
            is_weekend=self.IS_WEEKEND,
            is_adjacent=self.IS_ADJACENT,
            rule_id=self.RULE_ID,
        )
        expected = {
            "id": self.RULE_ID,
            "badge": self.BADGE_IMAGE,
            "name": self.RULE_NAME,
            "description": self.RULE_DESCRIPTION,
            "bonus": 0,
            "tasks_number": 0,
            "days_number": self.DAYS_NUMBER,
            "is_weekend": self.IS_WEEKEND,
            "is_adjacent": self.IS_ADJACENT,
        }

        self.assertDictEqual(expected, rule.to_dict())

    def test_project_rule_to_dict(self):
        rule = ProjectRule(
            task_type_name=self.TASK_TYPE_NAME,
            badge=self.BADGE_IMAGE,
            name=self.RULE_NAME,
            description=self.RULE_DESCRIPTION,
            bonus=0,
            tasks_number=0,
            days_number=self.DAYS_NUMBER,
            is_weekend=self.IS_WEEKEND,
            is_adjacent=self.IS_ADJACENT,
            rule_id=self.RULE_ID,
        )
        expected = {
            "id": self.RULE_ID,
            "badge": self.BADGE_IMAGE,
            "name": self.RULE_NAME,
            "description": self.RULE_DESCRIPTION,
            "bonus": 0,
            "tasks_number": 0,
            "days_number": self.DAYS_NUMBER,
            "is_weekend": self.IS_WEEKEND,
            "is_adjacent": self.IS_ADJACENT,
            "task_type_name": self.TASK_TYPE_NAME,
        }

        self.assertDictEqual(expected, rule.to_dict())
