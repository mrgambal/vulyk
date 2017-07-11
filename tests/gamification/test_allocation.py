# -*- coding: utf-8 -*-
"""
"""
from datetime import datetime
from decimal import Decimal
from vulyk.models.stats import WorkSession
from vulyk.models.tasks import AbstractTask, AbstractAnswer, Batch
from vulyk.models.user import User, Group

from .fixtures import FakeType
from ..base import BaseTest


class TestAllocationOfMoneyAndPoints(BaseTest):
    TASK_TYPE = FakeType.type_name
    TIMESTAMP = datetime.now()

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])

    def tearDown(self):
        User.objects.delete()
        Group.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        WorkSession.objects.delete()
        Batch.objects.delete()

        super().tearDown()

    def test_allocated_well(self):
        task_type = FakeType({})
        user = User(username='user0', email='user0@email.com').save()
        batch = Batch(
            id='default',
            task_type=self.TASK_TYPE,
            tasks_count=1,
            tasks_processed=0,
            batch_meta={
                "points_per_task": 1.0,
                "coins_per_task": 1.0
            }
        ).save()

        task = task_type.task_model(
            id='task0',
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={'data': 'data'}).save()

        task_type._work_session_manager.start_work_session(task, user.id)
        task_type.on_task_done(user, task.id, {'result': 'result'})
