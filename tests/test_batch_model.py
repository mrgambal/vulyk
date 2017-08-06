# -*- coding: utf-8 -*-
"""
test_batch_model
"""
from vulyk.models.tasks import Batch, BatchUpdateResult
from vulyk.signals import on_batch_done

from .base import BaseTest
from .fixtures import FakeType


class TestBatchModel(BaseTest):
    TASK_TYPE = FakeType.type_name

    def tearDown(self):
        Batch.objects.delete()

    def test_task_done_not_closing(self):
        batch = Batch(
            id='default',
            task_type=self.TASK_TYPE,
            tasks_count=5,
            tasks_processed=3,
            closed=False,
            batch_meta={}
        ).save()
        called_times = 0

        @on_batch_done.connect
        def listen(sender: Batch) -> None:
            nonlocal called_times, batch
            assert (sender.id == batch.id), 'Wrong sender {!r}'.format(sender)
            called_times += 1

        result = Batch.task_done_in(batch.id)
        batch.reload()

        self.assertEqual(result, BatchUpdateResult(True, False))
        self.assertFalse(batch.closed)
        self.assertEqual(batch.tasks_processed, 4)
        self.assertEqual(called_times, 0)

    def test_task_done_closing(self):
        batch = Batch(
            id='default',
            task_type=self.TASK_TYPE,
            tasks_count=5,
            tasks_processed=4,
            closed=False,
            batch_meta={}
        ).save()
        called_times = 0

        @on_batch_done.connect
        def listen(sender: Batch) -> None:
            nonlocal called_times, batch
            assert(sender.id == batch.id), 'Wrong sender {!r}'.format(sender)
            called_times += 1

        result = Batch.task_done_in(batch.id)
        batch.reload()

        self.assertEqual(result, BatchUpdateResult(True, True))
        self.assertTrue(batch.closed)
        self.assertEqual(batch.tasks_processed, 5)
        self.assertEqual(called_times, 1)

    def test_task_done_closing_closed(self):
        batch = Batch(
            id='default',
            task_type=self.TASK_TYPE,
            tasks_count=5,
            tasks_processed=5,
            closed=True,
            batch_meta={}
        ).save()
        called_times = 0

        @on_batch_done.connect
        def listen(sender: Batch) -> None:
            nonlocal called_times, batch
            assert(sender.id == batch.id), 'Wrong sender {!r}'.format(sender)
            called_times += 1

        result_second = Batch.task_done_in(batch.id)
        batch.reload()

        self.assertEqual(result_second, BatchUpdateResult(False, False))
        self.assertTrue(batch.closed)
        self.assertEqual(batch.tasks_processed, 5)
        self.assertEqual(called_times, 0)
