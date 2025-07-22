# -*- coding: utf-8 -*-
"""
Classes within the package are supposed to be intermittent containers between
JSON sources and final queries. Everything that has anything to do with images,
representation and other specifications also goes here.
"""

__all__ = ["ProjectRule", "Rule", "RuleValidationException"]


class RuleValidationException(Exception):
    """
    Basic exception class for all types of rule validation violations.
    """


class Rule:
    """
    Base class for all rule containers.
    Those rules may be interpreted like the following:

    - you closed n tasks
    - you closed n tasks in m days
    - you closed n tasks in weekends
    - you've been working for m weekends
    - you've been working for m days in a row
    - you've been working for m weekends in a row

    Also additional bonuses to be given after user gets the achievement are
    included as well as achievement and its badge is.
    """

    __slots__ = [
        "_days_number",
        "_hash",
        "_is_adjacent",
        "_is_weekend",
        "_tasks_number",
        "badge",
        "bonus",
        "description",
        "name",
    ]

    def __init__(
        self,
        rule_id: str,
        badge: str,
        name: str,
        description: str,
        bonus: int,
        tasks_number: int,
        days_number: int,
        *,
        is_weekend: bool,
        is_adjacent: bool,
    ) -> None:
        """
        :param rule_id: Unique rule identifier.
        :param badge: Badge image (either base64 or URL).
        :param name: Achievement name.
        :param description: Achievement textual description.
        :param bonus: How much additional points we give for the achievement.
        :param tasks_number: Number of tasks needed to achieve.
        :param days_number: Number of days needed to achieve.
        :param is_weekend: Should this achievement be tied up with weekends?
        :param is_adjacent: Must it be given for work in adjacent days?
        """
        self.badge = badge
        self.name = name
        self.description = description
        self.bonus = bonus

        self._tasks_number = tasks_number
        self._days_number = days_number
        self._is_weekend = is_weekend
        self._is_adjacent = is_adjacent

        self._hash = rule_id

        self._validate()

    def _validate(self) -> None:
        """
        Verifies that the rule complies to internal invariants. Otherwise -
        the exception must be thrown.

        :raises: RuleValidationException
        """
        # no achievements for n tasks closed on m adjacent days/weekends
        # might be extended later
        if self._is_adjacent:
            if self._tasks_number > 0:
                raise RuleValidationException(
                    "Counting number of tasks closed in adjacent days/weekends is not supported."
                )
            if self._days_number == 0:
                raise RuleValidationException('Can not set "adjacent" flag with zero days')

        if self._tasks_number == 0 and self._days_number == 0:
            raise RuleValidationException("There must be at least one numeric bound")

    @property
    def id(self) -> str:
        return self._hash

    @property
    def tasks_number(self) -> int:
        return self._tasks_number

    @property
    def days_number(self) -> int:
        return self._days_number

    @property
    def is_weekend(self) -> bool:
        return self._is_weekend

    @property
    def is_adjacent(self) -> bool:
        return self._is_adjacent

    @property
    def limit(self) -> int:
        """
        The vital characteristic of the rule: the limit member should surpass
        to get the achievement.
        At current stage the property relies upon two values: tasks done by
        user and days he spent working on these tasks. The priority is
        following: if tasks number is specified, it always supersedes days.

        E.g.: if rule has `tasks_number=20` and `days_number=7` - limit is 20.
        We take the number of tasks done in 7 days, and compare it to 20.
        Otherwise, if only `days_number=7` is specified, limit is 7. We group
        all tasks were done not earlier than 7 days ago, group them by day and
        check if 7 items is returned from aggregation pipeline.

        :return: The value to be compared to aggregation results.
        """
        return self._tasks_number if (self._tasks_number or 0) > 0 else (self._days_number or 0)

    def to_dict(self) -> dict[str, str | int | bool]:
        """
        Could be used as a source for JSON or any other representation format

        :return: Dict-ized object view.
        """
        return {
            "id": self.id,
            "badge": self.badge,
            "name": self.name,
            "description": self.description,
            "bonus": self.bonus,
            "tasks_number": self.tasks_number,
            "days_number": self.days_number,
            "is_weekend": self.is_weekend,
            "is_adjacent": self.is_adjacent,
        }

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Rule):
            return self._hash == o.id

        return False

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return "Rule({name}, {bonus}, {tasks}, {days}, {week}, {adj})".format(
            name=self.name,
            bonus=self.bonus,
            tasks=self._tasks_number,
            days=self._days_number,
            week=self._is_weekend,
            adj=self._is_adjacent,
        )

    def __repr__(self) -> str:
        return "Rule({name}, {descr})".format(
            name=self.name,
            descr=self.description[:50] + "...",
        )


class ProjectRule(Rule):
    """
    Container for project specific rules.
    """

    __slots__ = [*Rule.__slots__, "_task_type_name"]

    def __init__(
        self,
        rule_id: str,
        task_type_name: str,
        badge: str,
        name: str,
        description: str,
        bonus: int,
        tasks_number: int,
        days_number: int,
        *,
        is_weekend: bool,
        is_adjacent: bool,
    ) -> None:
        """
        :param rule_id: Unique rule identifier.
        :param task_type_name: Task type name.
        :param badge: Badge image (either base64 or URL).
        :param name: Achievement name.
        :param description: Achievement textual description.
        :param bonus: How much additional points we give for the achievement.
        :param tasks_number: Number of tasks needed to achieve.
        :param days_number: Number of days needed to achieve.
        :param is_weekend: Should this achievement be tied up with weekends?
        :param is_adjacent: Must it be given for work in adjacent days?
        """
        super().__init__(
            rule_id=rule_id,
            badge=badge,
            name=name,
            description=description,
            bonus=bonus,
            tasks_number=tasks_number,
            days_number=days_number,
            is_weekend=is_weekend,
            is_adjacent=is_adjacent,
        )

        self._task_type_name = task_type_name

    @property
    def task_type_name(self) -> str:
        return self._task_type_name

    @classmethod
    def from_rule(cls, rule: Rule, task_type_name: str) -> Rule:
        """
        Factory method to extend regular Rule and promote it to ProjectRule

        :param rule: Basic Rule instance to copy info from.
        :param task_type_name: ID of the project/task type.

        :return: Fully formed ProjectRule.
        """
        return cls(
            rule_id=rule.id,
            task_type_name=task_type_name,
            badge=rule.badge,
            name=rule.name,
            description=rule.description,
            bonus=rule.bonus,
            tasks_number=rule.tasks_number,
            days_number=rule.days_number,
            is_weekend=rule.is_weekend,
            is_adjacent=rule.is_adjacent,
        )

    def to_dict(self) -> dict[str, str | int | bool]:
        """
        Could be used as a source for JSON or any other representation format.

        :return: Dict-ized object view.
        """
        result = super().to_dict()
        result["task_type_name"] = self.task_type_name

        return result

    def __str__(self) -> str:
        return "ProjectRule({name}, {task_type}, {bonus}, {tasks}, {days}, {week}, {adj})".format(
            name=self.name,
            task_type=self._task_type_name,
            bonus=self.bonus,
            tasks=self._tasks_number,
            days=self._days_number,
            week=self._is_weekend,
            adj=self._is_adjacent,
        )

    def __repr__(self) -> str:
        return "ProjectRule({name}, {task_type}, {descr})".format(
            name=self.name, task_type=self._task_type_name, descr=self.description[:50] + "..."
        )

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ProjectRule):
            return self._hash == o.id

        return False

    def __ne__(self, o: object) -> bool:
        return not self == o
