# -*- coding: utf-8 -*-
"""
Classes within the package are supposed to be intermittent containers between
JSON sources and final queries. Everything that has anything to do with images,
representation and other specifications also goes here.
"""
__all__ = [
    'Rule',
    'ProjectRule',
    'RuleValidationException'
]


class RuleValidationException(Exception):
    pass


class Rule:
    """
    Base class for all rule containers.
    Those rules may be interpreted like the following:

    - you closed n tasks
    - you closed n tasks in m days
    - you closed n tasks in mornings in m days
    - you closed n tasks in weekends
    - you've been working for m weekends
    - you've been working for m days in a row
    - you've been working for m weekends in a row

    Also additional bonuses to be given after user gets the achievement are
    included as well as achievement and its badge is.
    """

    def __init__(self,
                 id: int,
                 badge: str,
                 name: str,
                 description: str,
                 bonus: int,
                 tasks_number: int,
                 days_number: int,
                 is_weekend: bool,
                 is_adjacent: bool) -> None:
        """
        :param id: Raw JSON representation hash.
        :type id: int
        :param badge: Badge image (either base64 or URL)
        :type badge: str
        :param name: Achievement name
        :type name: str
        :param description: Achievement textual description
        :type description: str
        :param bonus: How much additional points we give for the achievement
        :type bonus: int
        :param tasks_number: Number of tasks needed to achieve
        :type tasks_number: int
        :param days_number: Number of days needed to achieve
        :type days_number: int
        :param is_weekend: Should this achievement be tied up with weekends?
        :type is_weekend: bool
        :param is_adjacent: Must it be given for work in adjacent days?
        :type is_adjacent: bool
        """
        self.badge = badge
        self.name = name
        self.description = description
        self.bonus = bonus

        self._tasks_number = tasks_number
        self._days_number = days_number
        self._is_weekend = is_weekend
        self._is_adjacent = is_adjacent

        self._hash = id

        self._validate()

    def _validate(self):
        """
        Verifies that the rule complies to internal invariants. Otherwise –
        the exception must be thrown.

        :raises: RuleValidationException
        """
        # no achievements for n tasks closed on m adjacent days/weekends
        # might be extended later
        if self._is_adjacent:
            if self._tasks_number > 0:
                raise RuleValidationException(
                    'Counting number of tasks closed in adjacent days/weekends'
                    ' is not supported.')
            elif self._days_number == 0:

                raise RuleValidationException(
                    'Can not set "adjacent" flag with zero days')

        if self._tasks_number == 0 and self._days_number == 0:
            raise RuleValidationException('There must be at least one '
                                          'numeric bound')

    @property
    def id(self):
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
    def limit(self):
        return self._tasks_number \
            if self._tasks_number > 0 \
            else self._days_number

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Rule):
            return self._hash == o.id
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return 'Rule({name}, {bonus}, {tasks}, {days}, {week}, {adj})'.format(
            name=self.name,
            bonus=self.bonus,
            tasks=self._tasks_number,
            days=self._days_number,
            week=self._is_weekend,
            adj=self._is_adjacent
        )

    def __repr__(self) -> str:
        return 'Rule({name}, {descr})'.format(
            name=self.name,
            descr=self.description[:50] + '...',
        )


class ProjectRule(Rule):
    """
    Container for project specific rules.
    """

    def __init__(self,
                 id: int,
                 task_type_name: str,
                 badge: str,
                 name: str,
                 description: str,
                 bonus: int,
                 tasks_number: int,
                 days_number: int,
                 is_weekend: bool,
                 is_adjacent: bool) -> None:
        """
        :param id: Raw JSON representation hash.
        :type id: int
        :param task_type_name: ID of the project/task type.
        :type task_type_name: str
        :param badge: Badge image (either base64 or URL)
        :type badge: str
        :param name: Achievement name
        :type name: str
        :param description: Achievement textual description
        :type description: str
        :param bonus: How much additional points we give for the achievement
        :type bonus: int
        :param tasks_number: Number of tasks needed to achieve
        :type tasks_number: int
        :param days_number: Number of days needed to achieve
        :type days_number: int
        :param is_weekend: Should this achievement be tied up with weekends?
        :type is_weekend: bool
        :param is_adjacent: Must it be given for work in adjacent days?
        :type is_adjacent: bool
        """
        super().__init__(id=id,
                         badge=badge,
                         name=name,
                         description=description,
                         bonus=bonus,
                         tasks_number=tasks_number,
                         days_number=days_number,
                         is_weekend=is_weekend,
                         is_adjacent=is_adjacent)

        self._task_type_name = task_type_name

    @property
    def task_type_name(self) -> str:
        return self._task_type_name

    @classmethod
    def from_rule(cls, rule: Rule, task_type_name: str) -> Rule:
        """
        Factory method to extend regular Rule and promote it to ProjectRule

        :param rule: Basic Rule instance to copy info from
        :type rule: Rule
        :param task_type_name: ID of the project/task type.
        :type task_type_name: str

        :return: Fully formed ProjectRule
        :rtype: ProjectRule
        """
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
            is_adjacent=rule.is_adjacent)

    def __str__(self) -> str:
        return 'ProjectRule({name}, {task_type}, {bonus}, {tasks}, {days},' \
               ' {week}, {adj})' \
            .format(name=self.name,
                    task_type=self._task_type_name,
                    bonus=self.bonus,
                    tasks=self._tasks_number,
                    days=self._days_number,
                    week=self._is_weekend,
                    adj=self._is_adjacent)

    def __repr__(self) -> str:
        return 'ProjectRule({name}, {task_type}, {descr})'.format(
            name=self.name,
            task_type=self._task_type_name,
            descr=self.description[:50] + '...'
        )

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ProjectRule):
            return self._hash == o.id
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self == o
