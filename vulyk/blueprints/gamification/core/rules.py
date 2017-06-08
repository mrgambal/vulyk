# -*- coding: utf-8 -*-
"""
Classes within the package are supposed to be intermittent containers between
JSON sources and final queries. Everything that has anything to do with images,
representation and other specifications also goes here.
"""


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
                 badge: str,
                 name: str,
                 description: str,
                 bonus: int,
                 tasks_number: int,
                 days_number: int,
                 is_weekend: bool,
                 is_adjacent: bool,
                 string: str) -> None:
        """
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
        :param string: Raw JSON representation.
        :type string: str
        """
        self.badge = badge
        self.name = name
        self.description = description
        self.bonus = bonus

        self._tasks_number = tasks_number
        self._days_number = days_number
        self._is_weekend = is_weekend
        self._is_adjacent = is_adjacent

        self._string = string

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

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Rule):
            return o.badge == self.badge \
                and o.name == self.name \
                and o.description == self.description \
                and o.bonus == self.bonus \
                and o._tasks_number == self._tasks_number \
                and o._days_number == self._days_number \
                and o._is_weekend == self._is_weekend \
                and o._is_adjacent == self._is_adjacent
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
                 task_type_name: str,
                 badge: str,
                 name: str,
                 description: str,
                 bonus: int,
                 tasks_number: int,
                 days_number: int,
                 is_weekend: bool,
                 is_adjacent: bool,
                 string: str) -> None:
        """
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
        :param string: Raw JSON representation.
        :type string: str
        """
        super().__init__(badge,
                         name,
                         description,
                         bonus,
                         tasks_number,
                         days_number,
                         is_weekend,
                         is_adjacent,
                         string)

        self._task_type_name = task_type_name

    @property
    def task_type_name(self) -> str:
        return self._task_type_name

    @classmethod
    def from_rule(cls, rule: Rule, task_type_name: str, string: str) -> Rule:
        """
        Factory method to extend regular Rule and promote it to ProjectRule

        :param rule: Basic Rule instance to copy info from
        :type rule: Rule
        :param task_type_name: ID of the project/task type.
        :type task_type_name: str
        :param string: Raw JSON representation.
        :type string: str

        :return: Fully formed ProjectRule
        :rtype: ProjectRule
        """
        return cls(
            task_type_name,
            rule.badge,
            rule.name,
            rule.description,
            rule.bonus,
            rule.tasks_number,
            rule.days_number,
            rule.is_weekend,
            rule.is_adjacent,
            string)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, ProjectRule):
            return super().__eq__(o) \
                   and self._task_type_name == o._task_type_name
        else:
            return False

    def __ne__(self, o: object) -> bool:
        return not self == o

    def __str__(self) -> str:
        return 'ProjectRule({name}, {task_type}, {bonus}, {tasks}, {days},' \
               ' {week}, {adj})'\
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
