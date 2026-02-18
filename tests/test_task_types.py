#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_task_types
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from bson import ObjectId

from vulyk.ext.leaderboard import LeaderBoardManager
from vulyk.models.exc import (
    InitializationError,
    TaskImportError,
    TaskNotFoundError,
    TaskValidationError,
    WorkSessionLookUpError,
)
from vulyk.models.stats import WorkSession
from vulyk.models.task_types import AbstractTaskType
from vulyk.models.tasks import AbstractAnswer, AbstractTask, Batch
from vulyk.models.user import Group, User

from .base import BaseTest
from .fixtures import FakeType


class TestTaskTypes(BaseTest):
    TASK_TYPE = FakeType.type_name

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(description="test", id="default", allowed_types=[cls.TASK_TYPE])

    @classmethod
    def tearDownClass(cls):
        Group.objects.delete()

        super().tearDownClass()

    def tearDown(self):
        User.objects.delete()
        AbstractTask.objects.delete()
        AbstractAnswer.objects.delete()
        Batch.objects.delete()
        WorkSession.objects.delete()

        super().tearDown()

    # region Task type
    def test_init_task_inheritance(self):
        class NoTask(AbstractTaskType):
            task_model = Mock

        self.assertRaises(InitializationError, lambda: NoTask({}))

    def test_init_answer_inheritance(self):
        class NoAnswer(AbstractTaskType):
            task_model = AbstractTask
            answer_model = Mock

        self.assertRaises(InitializationError, lambda: NoAnswer({}))

    def test_init_type_name(self):
        class NoTypeName(AbstractTaskType):
            task_model = AbstractTask
            answer_model = AbstractAnswer

        self.assertRaises(InitializationError, lambda: NoTypeName({}))

    def test_init_template_name(self):
        class NoTemplateName(AbstractTaskType):
            task_model = AbstractTask
            answer_model = AbstractAnswer
            type_name = "FakeTaskType"

        self.assertRaises(InitializationError, lambda: NoTemplateName({}))

    @patch("mongoengine.queryset.base.BaseQuerySet.count", lambda *a: 22)
    def test_to_dict(self):
        got = {
            "name": "Fake name",
            "description": "Fake description",
            "type": "FakeTaskType",
            "tasks": 22,
            "closed_tasks": 22,
            "open_tasks": 0,
            "has_tasks": False,
        }

        self.assertDictEqual(FakeType({}).to_dict(), got)

    # endregion Task type

    # region Import tasks
    def test_import_tasks(self):
        tasks = ({"name": "1"}, {"name": "2"}, {"name": "3"})
        repo = FakeType({})

        repo.import_tasks(tasks, "default")

        self.assertEqual(len(FakeType.task_model.objects()), len(tasks))
        self.assertEqual(repo.task_model.objects.count(), len(tasks))

    def test_import_tasks_not_dict(self):
        tasks = [{"name": "1"}, (), {"name": "3"}]

        self.assertRaises(TaskImportError, lambda: FakeType({}).import_tasks(tasks, "default"))

    def test_import_tasks_not_list(self):
        self.assertRaises(TaskImportError, lambda: FakeType({}).import_tasks({"name": "1"}, "default"))

    def test_import_fails_when_overwriting(self):
        tasks = [{"name": "0"}, {"name": "1"}, {"name": "1"}, {"name": "2"}]
        repo = FakeType({})

        self.assertRaises(TaskImportError, lambda: repo.import_tasks(tasks, "default"))
        self.assertEqual(repo.task_model.objects.count(), 2)

    # endregion Import tasks

    # region Export reports
    def test_export_reports_normal(self):
        reports = []
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=2, tasks_processed=0).save()
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=True,
                users_count=2,
                users_processed=[user],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(timezone.utc),
                task_type=task_type.type_name,
                result={},
            ).save()
            reports.append([report.as_dict()])

        self.assertCountEqual(task_type.export_reports(batch=batch), reports)

    def test_export_reports_batch(self):
        reports = []
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batches = [
            Batch(id="batch%i" % i, task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
            for i in range(2)
        ]
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=batches[i],
                closed=True,
                users_count=2,
                users_processed=[user],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(timezone.utc),
                task_type=task_type.type_name,
                result={},
            ).save()
            reports.append([report.as_dict()])

        self.assertCountEqual(task_type.export_reports(batch=batches[1]), reports[1:])

    def test_export_reports_batch_with_no_closed(self):
        """
        The case when we export the batch where no task is closed.
        Yield must be empty.
        """
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batches = [
            Batch(id="batch%i" % i, task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
            for i in range(2)
        ]
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=batches[i],
                closed=not bool(i),
                users_count=2,
                users_processed=[user],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]
        for i in range(len(tasks)):
            task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(timezone.utc),
                task_type=task_type.type_name,
                result={},
            ).save()

        self.assertCountEqual(task_type.export_reports(batch=batches[1]), [])

    def test_export_reports_one_is_closed(self):
        reports = []
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=2, tasks_processed=0).save()
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=bool(i),
                users_count=2,
                users_processed=[user],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(timezone.utc),
                task_type=task_type.type_name,
                result={},
            ).save()
            reports.append([report.as_dict()])

        self.assertCountEqual(task_type.export_reports(batch=batch), reports[1:])

    def test_export_all_reports(self):
        reports = []
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=2, tasks_processed=0).save()
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=bool(i),
                users_count=2,
                users_processed=[user],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]
        for i in range(len(tasks)):
            report = task_type.answer_model(
                task=tasks[i],
                created_by=user,
                created_at=datetime.now(timezone.utc),
                task_type=task_type.type_name,
                result={},
            ).save()
            reports.append([report.as_dict()])

        self.assertCountEqual(task_type.export_reports(batch=batch, closed=False), reports)

    def test_export_reports_with_sessions(self):
        """Session data (start, end, duration, activity) appears correctly."""
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=batch,
            closed=True,
            users_count=1,
            users_processed=[user],
            task_data={"data": "data"},
        ).save()
        answer = task_type.answer_model(
            task=task,
            created_by=user,
            created_at=datetime.now(timezone.utc),
            task_type=task_type.type_name,
            result={"r": 1},
        ).save()
        start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 10, 5, 0, tzinfo=timezone.utc)
        WorkSession(
            user=user,
            task=task,
            task_type=task_type.type_name,
            answer=answer,
            start_time=start,
            end_time=end,
            activity=120,
        ).save()

        results = list(task_type.export_reports(batch=batch, with_sessions=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 1)
        session_data = results[0][0]["session"]
        # MongoDB stores datetimes as naive UTC, so isoformat() lacks the +00:00 suffix
        self.assertIn("2024-01-01T10:00:00", session_data["start_time"])
        self.assertIn("2024-01-01T10:05:00", session_data["end_time"])
        self.assertEqual(session_data["duration"], 300)
        self.assertEqual(session_data["activity"], 120)

    def test_export_reports_with_sessions_no_session(self):
        """'session' key omitted when no session exists for an answer."""
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=batch,
            closed=True,
            users_count=1,
            users_processed=[user],
            task_data={"data": "data"},
        ).save()
        task_type.answer_model(
            task=task,
            created_by=user,
            created_at=datetime.now(timezone.utc),
            task_type=task_type.type_name,
            result={"r": 1},
        ).save()

        results = list(task_type.export_reports(batch=batch, with_sessions=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 1)
        self.assertNotIn("session", results[0][0])

    def test_export_reports_without_sessions_flag_unchanged(self):
        """Default behavior unchanged — no 'session' even when sessions exist in DB."""
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=batch,
            closed=True,
            users_count=1,
            users_processed=[user],
            task_data={"data": "data"},
        ).save()
        answer = task_type.answer_model(
            task=task,
            created_by=user,
            created_at=datetime.now(timezone.utc),
            task_type=task_type.type_name,
            result={"r": 1},
        ).save()
        WorkSession(
            user=user,
            task=task,
            task_type=task_type.type_name,
            answer=answer,
            start_time=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2024, 1, 1, 10, 5, 0, tzinfo=timezone.utc),
            activity=120,
        ).save()

        results = list(task_type.export_reports(batch=batch))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 1)
        self.assertNotIn("session", results[0][0])

    def test_export_reports_with_sessions_multiple_answers(self):
        """Correct per-answer matching when task has multiple answers/sessions."""
        task_type = FakeType({})
        user1 = User(username="user0", email="user0@email.com").save()
        user2 = User(username="user1", email="user1@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=batch,
            closed=True,
            users_count=2,
            users_processed=[user1, user2],
            task_data={"data": "data"},
        ).save()
        answer1 = task_type.answer_model(
            task=task,
            created_by=user1,
            created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            task_type=task_type.type_name,
            result={"r": 1},
        ).save()
        answer2 = task_type.answer_model(
            task=task,
            created_by=user2,
            created_at=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
            task_type=task_type.type_name,
            result={"r": 2},
        ).save()
        start1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        end1 = datetime(2024, 1, 1, 10, 3, 0, tzinfo=timezone.utc)
        start2 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        end2 = datetime(2024, 1, 1, 11, 10, 0, tzinfo=timezone.utc)
        WorkSession(
            user=user1,
            task=task,
            task_type=task_type.type_name,
            answer=answer1,
            start_time=start1,
            end_time=end1,
            activity=60,
        ).save()
        WorkSession(
            user=user2,
            task=task,
            task_type=task_type.type_name,
            answer=answer2,
            start_time=start2,
            end_time=end2,
            activity=300,
        ).save()

        results = list(task_type.export_reports(batch=batch, with_sessions=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 2)

        # Build a map by answer result to check session matching
        by_result = {r["answer"]["r"]: r for r in results[0]}
        self.assertEqual(by_result[1]["session"]["duration"], 180)
        self.assertEqual(by_result[1]["session"]["activity"], 60)
        self.assertEqual(by_result[2]["session"]["duration"], 600)
        self.assertEqual(by_result[2]["session"]["activity"], 300)

    # endregion Export reports

    # region Next task
    def test_batches_are_complete(self):
        task_type = FakeType({})
        Batch(id="default", task_type=task_type.type_name, tasks_count=2, tasks_processed=2).save()
        user = User(username="user0", email="user0@email.com").save()
        [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch="default",
                closed=True,
                users_count=0,
                users_processed=[],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]

        self.assertEqual(task_type.get_next(user), {}, "Should return an empty dict if all is done")

    def test_not_return_processed(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch="default",
                closed=False,
                users_count=1,
                users_processed=[user],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]

        self.assertEqual(task_type.get_next(user), {}, "Should return an empty dict if user passed all tasks")

    def test_return_proper_type(self):
        class NewFakeModel(AbstractTask):
            pass

        class NewFakeAnswer(AbstractAnswer):
            pass

        class NewFakeType(AbstractTaskType):
            task_model = NewFakeModel
            answer_model = NewFakeAnswer
            type_name = "NewFakeTaskType"
            template = "tmpl.html"

            _name = "New Fake name"
            _description = "New Fake description"

        old_task_type = FakeType({})
        task_type = NewFakeType({})

        group = Group(description="test", id="test", allowed_types=[self.TASK_TYPE, task_type.type_name]).save()
        user = User(username="user0", email="user0@email.com", groups=[group]).save()
        task_type.task_model(
            id="task1",
            task_type=task_type.type_name,
            batch="default",
            closed=False,
            users_count=0,
            users_processed=[],
            task_data={"data": "data"},
        ).save()

        self.assertEqual(old_task_type.get_next(user), {}, "Should return no task of another type")

    def test_not_show_skipped_until_nothing_else_left(self):
        task_type = FakeType({})
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=2, tasks_processed=0).save()
        user = User(username="user0", email="user0@email.com").save()
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=batch,
                closed=False,
                users_count=0,
                users_processed=[],
                users_skipped=[user][: i % 2],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]
        # that's how we deal with randomized yield
        for _ in range(5):
            self.assertEqual(task_type.get_next(user), tasks[0].as_dict(), "Should return only task that isn't skipped")

    def test_return_skipped_if_none_else_left(self):
        task_type = FakeType({})
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[user],
            task_data={"data": "data"},
        ).save()

        self.assertEqual(
            task_type.get_next(user), task.as_dict(), "Should return even skipped task if nothing else is available"
        )

    def test_fallback_to_any_batch(self):
        task_type = FakeType({})
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=1).save()
        user = User(username="user0", email="user0@email.com").save()
        tasks = [
            task_type.task_model(
                id="task%s" % i,
                task_type=task_type.type_name,
                batch=[batch, "default"][i],
                closed=not bool(i),
                users_count=1 - i,
                users_processed=[user][: 1 - i],
                users_skipped=[],
                task_data={"data": "data"},
            ).save()
            for i in range(2)
        ]

        for _ in range(5):
            self.assertEqual(task_type.get_next(user), tasks[1].as_dict(), "Should return only task that isn't skipped")

    def test_return_skipped_if_none_else_left_no_batch(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch="any_batch",
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[user],
            task_data={"data": "data"},
        ).save()

        self.assertEqual(
            task_type.get_next(user), task.as_dict(), "Should return even skipped task if nothing else is available"
        )

    # endregion Next task

    # region Skip task
    def test_skip_task_normal(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()

        task_type._work_session_manager.start_work_session(task, user)
        task_type.skip_task(task.id, user)

        task.reload()

        self.assertEqual(task.users_skipped, [user])

    def test_skip_task_twice(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()

        task_type._work_session_manager.start_work_session(task, user)
        task_type.skip_task(task.id, user)

        self.assertRaises(WorkSessionLookUpError, lambda: task_type.skip_task(task.id, user))

        task.reload()

        self.assertEqual(task.users_skipped, [user])

    def test_skip_raises_not_found(self):
        self.assertRaises(TaskNotFoundError, lambda: FakeType({}).skip_task("fake_id", {}))

    # endregion Skip task

    # region On task done
    def test_on_done_ok(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()

        task_type._work_session_manager.start_work_session(task, user.id)
        task_type.on_task_done(user, task.id, {"result": "result"})

        task.reload()
        user = User.objects.get(id=user.id)

        self.assertEqual(task.users_count, 1)
        self.assertEqual(task.users_processed, [user])
        self.assertEqual(user.processed, 1)

    def test_on_done_twice_fires_exception(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=0,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        task_type._work_session_manager.start_work_session(task, user.id)

        task_type.on_task_done(user, task.id, {"result": "result"})

        self.assertRaises(TaskValidationError, lambda: task_type.on_task_done(user, task.id, {"result": "result2"}))

    def test_on_done_close_task(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=None,
            closed=False,
            users_count=2,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        task_type._work_session_manager.start_work_session(task, user.id)

        task_type.on_task_done(user, task.id, {"result": "result"})

        task.reload()

        self.assertTrue(task.closed)

    def test_on_done_alter_batch(self):
        task_type = FakeType({})
        user = User(username="user0", email="user0@email.com").save()
        batch = Batch(id="default", task_type=task_type.type_name, tasks_count=1, tasks_processed=0).save()
        task = task_type.task_model(
            id="task0",
            task_type=task_type.type_name,
            batch=batch,
            closed=False,
            users_count=2,
            users_processed=[],
            users_skipped=[],
            task_data={"data": "data"},
        ).save()
        task_type._work_session_manager.start_work_session(task, user.id)

        task_type.on_task_done(user, task.id, {"result": "result"})

        batch = Batch.objects.get(id=batch.id)

        self.assertEqual(batch.tasks_processed, 1)

    def test_on_done_raises_not_found(self):
        self.assertRaises(
            TaskNotFoundError,
            lambda: FakeType({}).on_task_done(User(username="user0", email="user0@email.com"), "fake_id", {}),
        )

    # endregion On task done

    # region Leaders
    def test_proxy_leaderboard_get_leaders(self):
        fake_type = FakeType({})
        fake_manager = Mock(spec=LeaderBoardManager)
        answer = [(ObjectId(), 15), (ObjectId(), 2)]
        fake_manager.get_leaders = lambda: answer
        fake_type._leaderboard_manager = fake_manager

        self.assertEqual(fake_type.get_leaders(), answer, "AbstractTaskType should not change leaders list")

    def test_proxy_leaderboard_get_leaderboard(self):
        fake_type = FakeType({})
        fake_manager = Mock(spec=LeaderBoardManager)
        answer = [{"username": "user1", "freq": 12}, {"username": "user2", "freq": 10}]
        fake_manager.get_leaderboard = lambda limit: answer
        fake_type._leaderboard_manager = fake_manager

        self.assertEqual(fake_type.get_leaderboard(), answer, "AbstractTaskType should not change leaderboard")

    # endregion Leaders


if __name__ == "__main__":
    unittest.main()
