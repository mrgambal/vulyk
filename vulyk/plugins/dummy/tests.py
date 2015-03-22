# coding=utf-8

import unittest

import mongomock

from .dummy import DummyTask, DummyAnswer, DummyTaskType


class TestDummyTask(unittest.TestCase):

    def test_taskstore(self):
        collection = mongomock.Connection().db.collection

        class MockedDummyTask(DummyTask):

            meta = {
                'collection': collection,
                'allow_inheritance': True,
                'indexes': [
                    'task_type'
                ]
            }

        dummy_tasks = [{"a": 3, "b": 1}, {"a": 7, "b": 4}, {"a": 2, "b": 9}]

        dummy_tasks_objs = [
            MockedDummyTask(task_type='dummy_task', task_data=task_data)
            for task_data in dummy_tasks
        ]


if __name__ == '__main__':
    unittest.main()
