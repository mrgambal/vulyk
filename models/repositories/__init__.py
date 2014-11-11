# coding=utf-8
import abc
import random
from slug import slug
from transliterate import translit

from ..tasks import Task, Report


class AbstractRepository(object):
    __metaclass__ = abc.ABCMeta
    _instance = None
    _model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance


class TaskRepository(AbstractRepository):
    _model = Task

    def load_from_dict(self, data):
        """
        Creates a new item using data coming from JSON

        :param data: Data-dictionary from JSON
        :return: ID of new task
        :rtype str:
        """

        task = self._model(**data)
        task.id = slug(translit(task.title[:25], "uk", reversed=True))
        task.save()

        return task.id

    def get_next_task(self, user, redundancy=2):
        """
        Find here Task that processed less than app.config.USERS_PER_TASK
        And wasn't processed by current user

        :type user: User
        :type redundancy: int
        :rtype: Task
        """
        res = self._model.objects(
            users_count__lt=redundancy,
            users_processed__ne=user
        ).no_dereference()
        res = res[random.randint(0, res.count())]

        return res

    def save_on_success(self, data, user):
        """
        Find here Task that processed less than app.config.USERS_PER_TASK
        And wasn't processed by current user

        :type data: dict
        :type user: User
        :rtype: Task
        """
        res = self._model.objects.get_or_404(_id=data.get("pk", -1))
        res.users_processed.push(user)
        res.users_count += 1

        return res.save()


class ReportRepository(AbstractRepository):
    _model = Report

    def create(self, task, user, mistakes):
        """
        Creates new report after user finished a task.

        :param task:
        :type task: Task
        :param user:
        :type user: User
        :param mistakes:
        :type mistakes: list[dict]

        :return: True if successful
        :rtype : bool
        """
        res = self._model.objects.create(
            task=task,
            created_by=user,
            found_mistakes=mistakes)

        return res is not None
