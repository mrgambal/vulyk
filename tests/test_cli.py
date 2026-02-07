#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
"""

import gzip
import unittest
from datetime import datetime, timezone
from typing import Any, ClassVar

import bz2file
import click
from click.testing import CliRunner

from vulyk.cli import admin, batches, db, is_initialized, project_init
from vulyk.control import batch_remove, cli
from vulyk.models.stats import WorkSession
from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractAnswer, AbstractTask, Batch
from vulyk.models.user import Group, User

from .base import BaseTest
from .fixtures import FakeType


class TestAdmin(BaseTest):
    @classmethod
    def setUpClass(cls) -> None:
        Group(id="default", description="test", allowed_types=[FakeType.type_name]).save()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        Group.objects.delete()

        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()

        for i in range(1, 4):
            User(username="1", email="%s@email.com" % i, admin=i % 3 == 0).save()

    def tearDown(self) -> None:
        User.objects.delete()

        super().tearDown()

    def test_toggle_admin(self) -> None:
        admin.toggle_admin("1@email.com", state=False)
        admin.toggle_admin("2@email.com", state=True)
        admin.toggle_admin("3@email.com", state=True)

        self.assertFalse(User.objects.get(email="1@email.com").admin)
        self.assertTrue(User.objects.get(email="2@email.com").admin)
        self.assertTrue(User.objects.get(email="3@email.com").admin)


class TestDB(BaseTest):
    def test_open_anything(self) -> None:
        filename = "test.bz2"
        self.assertEqual(db.open_anything(filename), bz2file.BZ2File)
        filename = "test.gz"
        self.assertEqual(db.open_anything(filename), gzip.open)


class TestBatches(BaseTest):
    TASK_TYPE_NAME = "declaration_task"

    class TestTaskType(AbstractTaskType):
        answer_model = AbstractAnswer
        task_model = AbstractTask
        type_name = "declaration_task"
        template = "some_template"
        _task_type_meta: ClassVar[dict[str, Any]] = {
            "foo": "bar",
            "int": 1,
            "float": 0.1,
            "bool1": False,
            "bool2": True,
        }

    class AnotherTaskType(TestTaskType):
        type_name = "wrong_task"

    DEFAULT_BATCH = "default"
    TASK_TYPE = TestTaskType({})
    WRONG_TASK_TYPE = AnotherTaskType({})

    def tearDown(self) -> None:
        WorkSession.objects.delete()
        AbstractAnswer.objects.delete()
        AbstractTask.objects.delete()
        Batch.objects.delete()
        User.objects.delete()
        Group.objects.delete()

        super().tearDown()

    def test_add_default_batch(self) -> None:
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)
        self.assertEqual(
            batch.batch_meta,
            {
                "foo": "bar",
                "int": 1,
                "float": 0.1,
                "bool1": False,
                "bool2": True,
            },
        )

    def test_override_meta_information(self) -> None:
        batches.add_batch(
            self.DEFAULT_BATCH,
            10,
            self.TASK_TYPE,
            self.DEFAULT_BATCH,
            batch_meta={"foo": "barbaz", "bool1": "true", "bool2": "false"},
        )

        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)
        self.assertEqual(batch.batch_meta, {"foo": "barbaz", "int": 1, "float": 0.1, "bool1": True, "bool2": False})

    def test_broken_meta1(self) -> None:
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(
                self.DEFAULT_BATCH, 10, self.TASK_TYPE, self.DEFAULT_BATCH, batch_meta={"newshit": "justempty"}
            ),
        )

    def test_broken_meta2(self) -> None:
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(
                self.DEFAULT_BATCH, 10, self.TASK_TYPE, self.DEFAULT_BATCH, batch_meta={"int": "simplywrong"}
            ),
        )

    def test_add_new_tasks_to_default(self) -> None:
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch(self.DEFAULT_BATCH, 20, self.TASK_TYPE, self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=self.DEFAULT_BATCH)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 30)

    def test_add_wrong_task_type(self) -> None:
        batches.add_batch(self.DEFAULT_BATCH, 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        self.assertRaises(
            click.exceptions.BadParameter,
            lambda: batches.add_batch(self.DEFAULT_BATCH, 20, self.WRONG_TASK_TYPE, self.DEFAULT_BATCH),
        )

    def test_add_second_batch(self) -> None:
        batch_name = "new_batch"
        batches.add_batch(batch_name, 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=batch_name)

        self.assertEqual(batch.task_type, self.TASK_TYPE_NAME)
        self.assertEqual(batch.tasks_count, 10)
        self.assertEqual(batch.tasks_processed, 0)
        self.assertEqual(batch.batch_meta, {"foo": "bar", "int": 1, "float": 0.1, "bool1": False, "bool2": True})

    def test_extend_not_default_batch(self) -> None:
        batch_name = "new_batch"
        batches.add_batch(batch_name, 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        self.assertRaises(
            click.exceptions.BadParameter, lambda: batches.add_batch(batch_name, 20, self.TASK_TYPE, self.DEFAULT_BATCH)
        )

    def test_validate_batch(self) -> None:
        not_exists = "4"
        batches.add_batch("1", 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch("2", 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch("3", 10, self.TASK_TYPE, self.DEFAULT_BATCH)

        self.assertEqual(not_exists, batches.validate_batch(None, None, not_exists, self.DEFAULT_BATCH))

    def test_validate_batch_exists(self) -> None:
        exists = "3"
        batches.add_batch("1", 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch("2", 10, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch(exists, 10, self.TASK_TYPE, self.DEFAULT_BATCH)

        self.assertRaises(click.BadParameter, lambda: batches.validate_batch(None, None, exists, self.DEFAULT_BATCH))

    def _create_batch_with_data(self, batch_name: str) -> None:
        """Helper: creates a batch with 2 tasks, 2 answers and 2 work sessions."""
        batches.add_batch(batch_name, 2, self.TASK_TYPE, self.DEFAULT_BATCH)
        batch = Batch.objects.get(id=batch_name)

        if not Group.objects(id="default"):
            Group(id="default", description="test", allowed_types=[self.TASK_TYPE.type_name]).save()

        user = User(username="testuser", email="testuser@email.com").save()

        for i in range(2):
            task = AbstractTask(
                id="task%s" % i,
                task_type=self.TASK_TYPE.type_name,
                batch=batch,
                task_data={"data": "data"},
            ).save()

            AbstractAnswer(
                task=task,
                created_by=user,
                created_at=datetime.now(timezone.utc),
                task_type=self.TASK_TYPE.type_name,
                result={"result": "ok"},
            ).save()

            WorkSession(
                user=user,
                task=task,
                task_type=self.TASK_TYPE.type_name,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                activity=10,
            ).save()

    def test_remove_batch(self) -> None:
        batch_name = "to_remove"
        self._create_batch_with_data(batch_name)

        self.assertEqual(Batch.objects(id=batch_name).count(), 1)
        self.assertEqual(AbstractTask.objects(batch=batch_name).count(), 2)

        batches.remove_batch(batch_name)

        self.assertEqual(Batch.objects(id=batch_name).count(), 0)
        self.assertEqual(AbstractTask.objects(batch=batch_name).count(), 0)

    def test_remove_batch_with_purge(self) -> None:
        batch_name = "to_purge"
        self._create_batch_with_data(batch_name)

        self.assertEqual(AbstractAnswer.objects(task_type=self.TASK_TYPE.type_name).count(), 2)
        self.assertEqual(WorkSession.objects(task_type=self.TASK_TYPE.type_name).count(), 2)

        batches.remove_batch(batch_name, purge=True)

        self.assertEqual(Batch.objects(id=batch_name).count(), 0)
        self.assertEqual(AbstractTask.objects(batch=batch_name).count(), 0)
        self.assertEqual(AbstractAnswer.objects(task_type=self.TASK_TYPE.type_name).count(), 0)
        self.assertEqual(WorkSession.objects(task_type=self.TASK_TYPE.type_name).count(), 0)

    def test_remove_nonexistent_batch(self) -> None:
        self.assertRaises(click.BadParameter, lambda: batches.remove_batch("nonexistent"))

    def test_cli_batches_list(self) -> None:
        batches.add_batch("batch_a", 5, self.TASK_TYPE, self.DEFAULT_BATCH)
        batches.add_batch("batch_b", 3, self.TASK_TYPE, self.DEFAULT_BATCH)

        runner = CliRunner()
        result = runner.invoke(cli, ["batches", "list"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("batch_a", result.output)
        self.assertIn("batch_b", result.output)

    def test_cli_batches_del(self) -> None:
        batches.add_batch("cli_remove", 2, self.TASK_TYPE, self.DEFAULT_BATCH)
        self.assertEqual(Batch.objects(id="cli_remove").count(), 1)

        # Invoke callback directly since click.Choice is frozen at import time
        batch_remove.callback(bid="cli_remove", purge=False)

        self.assertEqual(Batch.objects(id="cli_remove").count(), 0)

    def test_cli_batches_del_with_purge(self) -> None:
        self._create_batch_with_data("cli_purge")

        self.assertEqual(AbstractAnswer.objects(task_type=self.TASK_TYPE.type_name).count(), 2)
        self.assertEqual(WorkSession.objects(task_type=self.TASK_TYPE.type_name).count(), 2)

        batch_remove.callback(bid="cli_purge", purge=True)

        self.assertEqual(Batch.objects(id="cli_purge").count(), 0)
        self.assertEqual(AbstractTask.objects(batch="cli_purge").count(), 0)
        self.assertEqual(AbstractAnswer.objects(task_type=self.TASK_TYPE.type_name).count(), 0)
        self.assertEqual(WorkSession.objects(task_type=self.TASK_TYPE.type_name).count(), 0)


class TestProjectInit(BaseTest):
    def setUp(self) -> None:
        super().setUp()
        # Ensure a clean state before each test
        Group.objects.delete()
        User.objects.delete()

    def tearDown(self) -> None:
        # Ensure a clean state after each test
        Group.objects.delete()
        User.objects.delete()
        super().tearDown()

    def test_is_initialized_and_project_init_creates_group(self) -> None:
        # Initially no default group => not initialized
        self.assertFalse(is_initialized())

        expected_allowed = ["foo", "bar"]
        project_init(expected_allowed)

        # Now the default group exists
        self.assertTrue(is_initialized())
        group = Group.objects.get(id="default")
        self.assertEqual(set(group.allowed_types), set(expected_allowed))

    def test_project_init_updates_group_and_attaches_users(self) -> None:
        # Create default group with a single allowed type, create users
        Group(id="default", description="default group", allowed_types=["old"]).save()

        for i in range(3):
            User(username=f"user{i}", email=f"user{i}@example.test").save()

        # Ensure users were created and initially the group has only "old"
        g = Group.objects.get(id="default")
        self.assertEqual(set(g.allowed_types), {"old"})

        # project_init should add a new allowed_type and attach the group to all users
        project_init(["foo", "old"])

        g = Group.objects.get(id="default")
        self.assertEqual(set(g.allowed_types), {"old", "foo"})

        users = User.objects()
        self.assertTrue(len(users) >= 3)
        for u in users:
            # user.groups is a list of Group documents
            self.assertTrue(any(group_ref.id == "default" for group_ref in u.groups))


if __name__ == "__main__":
    unittest.main()
