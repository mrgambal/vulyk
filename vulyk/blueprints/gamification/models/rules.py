# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import StringField, IntField, BooleanField

from ..core.rules import Rule, ProjectRule

__all__ = [
    'RuleModel'
]


class RuleModel(Document):
    """
    Database-specific rule representation
    """
    id = StringField(required=True, unique=True, primary_key=True)
    task_type_name = StringField()
    badge = StringField(required=True)
    name = StringField(required=True, max_length=255, unique=True)
    description = StringField(required=True)
    bonus = IntField(min_value=0)
    tasks_number = IntField(min_value=0, db_field='tasksNumber')
    days_number = IntField(min_value=0, db_field='daysNumber')
    is_weekend = BooleanField(default=False, db_field='isWeekend')
    is_adjacent = BooleanField(default=False, db_field='isAdjacent')

    meta = {
        'collection': 'gamification.rules',
        'allow_inheritance': True,
        'indexes': [
            'name',
            'task_type_name'
        ]
    }

    @classmethod
    def from_rule(cls, rule: Rule):
        """
        Rule to DB-specific model converter.

        :param rule: Current Rule instance
        :type rule: Rule

        :return: New RuleModel instance
        :rtype: RuleModel
        """
        task_type_name = rule.task_type_name \
            if isinstance(rule, ProjectRule) \
            else ''

        return cls(
            id=rule.id,
            task_type_name=task_type_name,
            badge=rule.badge,
            name=rule.name,
            description=rule.description,
            bonus=rule.bonus,
            tasks_number=rule.tasks_number,
            days_number=rule.days_number,
            is_weekend=rule.is_weekend,
            is_adjacent=rule.is_adjacent
        )

    def to_rule(self) -> Rule:
        """
        DB-specific model to Rule converter.

        :return: New Rule instance
        :rtype: Rule
        """
        rule = Rule(
            rule_id=self.id,
            badge=self.badge,
            name=self.name,
            description=self.description,
            bonus=self.bonus,
            tasks_number=self.tasks_number,
            days_number=self.days_number,
            is_weekend=self.is_weekend,
            is_adjacent=self.is_adjacent
        )

        if self.task_type_name:
            return ProjectRule.from_rule(
                rule=rule,
                task_type_name=self.task_type_name
            )
        else:
            return rule

    def __str__(self):
        return str(self.to_rule())

    def __repr__(self):
        return repr(self.to_rule())
