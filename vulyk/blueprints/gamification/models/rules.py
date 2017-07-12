# -*- coding: utf-8 -*-
from flask_mongoengine import Document
from mongoengine import StringField, IntField, BooleanField, Q

from ..core.rules import Rule, ProjectRule

__all__ = [
    'RuleModel'
]


class RuleModel(Document):
    """
    Database-specific rule representation
    """
    id = IntField(required=True, primary_key=True)
    batch_name = StringField()
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
            'batch_name'
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
        batch_name = rule.batch_name \
            if isinstance(rule, ProjectRule) \
            else ''

        return cls(
            id=rule.id,
            batch_name=batch_name,
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

        if self.batch_name:
            return ProjectRule.from_rule(
                rule=rule,
                batch_name=self.batch_name
            )
        else:
            return rule

    @classmethod
    def get_actual_rules(cls: type,
                         ids: list,
                         batch_name: str,
                         is_weekend: bool) -> list:
        """
        Prepare the list of rules to apply.
        Cutting off is possible by using different tiny yet smart heuristics.

        :param ids: A list of rules to be skipped for any reason
        :type ids: list[str]
        :param batch_name: Name of the batch the task is assigned to
        :type batch_name: str
        :param is_weekend: It today is a working day, there is no reason to
        check for rules that are weekend-backed.
        :type is_weekend: bool

        :return: An array of rules to be checked and assigned.
        :rtype: list[Rule]
        """
        base_q = Q()

        if len(ids) > 0:
            base_q &= Q(id__nin=ids)

        if batch_name is not None and len(batch_name) > 0:
            base_q &= (Q(batch_name=batch_name)
                       | Q(batch_name='')
                       | Q(batch_name__exists=False))

        if not is_weekend:
            base_q &= Q(is_weekend=False)

        return [rule_model.to_rule() for rule_model in cls.objects(base_q)]

    def __str__(self):
        return 'RuleModel({model})'.format(model=str(self.to_rule()))

    def __repr__(self):
        return 'RuleModel({model})'.format(model=repr(self.to_rule()))
