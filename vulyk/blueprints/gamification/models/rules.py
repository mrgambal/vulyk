# -*- coding: utf-8 -*-
from collections import Iterator

from flask_mongoengine import Document
from mongoengine import StringField, IntField, BooleanField, Q

from ..core.rules import Rule, ProjectRule

__all__ = [
    'RuleModel',
    'AllRules',
    'ProjectAndFreeRules',
    'StrictProjectRules'
]


class RuleFilter:
    """
    Abstract class shows the idea of rules query filtering invariants.
    """
    def to_query(self) -> Q:
        """
        Prepares a filtering query.

        :return: Prepared query instance.
        :rtype: Q
        """
        raise NotImplementedError('You must override the method in successors')

    def __ne__(self, o: object) -> bool:
        return not self == o


class AllRules(RuleFilter):
    """
    Should return all rules.
    """
    def to_query(self) -> Q:
        """
        Prepares a filtering query.

        :return: Prepared query instance.
        :rtype: Q
        """
        return Q()

    def __eq__(self, o: object) -> bool:
        return isinstance(o, AllRules)


class ProjectAndFreeRules(RuleFilter):
    """
    Should return all rules related to a certain project along with
    project-agnostic ones.
    """
    def __init__(self, task_type_name: str) -> None:
        self._task_type_name = task_type_name

    def to_query(self) -> Q:
        """
        Prepares a filtering query.

        :return: Prepared query instance.
        :rtype: Q
        """
        return (Q(task_type_name=self._task_type_name)
                | Q(task_type_name='')
                | Q(task_type_name__exists=False))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ProjectAndFreeRules):
            return self._task_type_name == o._task_type_name
        else:
            return False


class StrictProjectRules(RuleFilter):
    """
    Should return all rules related only to a certain project.
    """
    def __init__(self, task_type_name: str) -> None:
        self._task_type_name = task_type_name

    def to_query(self) -> Q:
        """
        Prepares a filtering query.

        :return: Prepared query instance.
        :rtype: Q
        """
        return Q(task_type_name=self._task_type_name)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, StrictProjectRules):
            return self._task_type_name == o._task_type_name
        else:
            return False


class RuleModel(Document):
    """
    Database-specific rule representation
    """
    id = StringField(required=True, primary_key=True)
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
            else ''  # type: str

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

    @classmethod
    def get_actual_rules(
        cls,
        skip_ids: list,
        rule_filter: RuleFilter,
        is_weekend: bool
    ) -> Iterator:
        """
        Prepare the list of rules to apply.
        Cutting off is possible by using different tiny yet smart heuristics.

        :param skip_ids: A list of rules to be skipped for any reason
        :type skip_ids: list[str]
        :param rule_filter: Prepared query container.
        :type rule_filter: RuleFilter
        :param is_weekend: If today is a working day, there is no reason to
            check for rules that are weekend-backed.
        :type is_weekend: bool

        :return: An array of rules to be checked and assigned.
        :rtype: Iterator[Rule]
        """
        base_q = rule_filter.to_query()

        if len(skip_ids) > 0:
            base_q &= Q(id__nin=skip_ids)

        if not is_weekend:
            base_q &= Q(is_weekend=False)

        yield from [rule_model.to_rule() for rule_model in cls.objects(base_q)]

    def __str__(self) -> str:
        return 'RuleModel({model})'.format(model=str(self.to_rule()))

    def __repr__(self) -> str:
        return 'RuleModel({model})'.format(model=repr(self.to_rule()))
