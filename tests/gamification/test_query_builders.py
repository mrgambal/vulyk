# -*- coding: utf-8 -*-
"""
test_rule_parsing
"""
from datetime import date, datetime, timedelta

from bson import ObjectId

from vulyk.blueprints.gamification.core.queries import (
    MongoRuleExecutor,
    MongoRuleQueryBuilder)
from vulyk.blueprints.gamification.core.rules import Rule, ProjectRule
from vulyk.models.stats import WorkSession

from ..base import BaseTest


class TestMongoQueryBuilder(BaseTest):
    def test_n_tasks(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [{'$match': {'user': user_id}}]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_n_tasks_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            task_type_name=project,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'taskType': project}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_n_tasks_m_days(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=7,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = datetime.combine(date.today() - timedelta(days=7),
                                datetime.min.time())
        expected = [
            {'$match': {'user': user_id, 'end_time': {'$gt': then}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_n_tasks_m_days_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            task_type_name=project,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=7,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = datetime.combine(date.today() - timedelta(days=7),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'end_time': {'$gt': then},
                'taskType': project}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_n_tasks_weekends(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_n_tasks_weekends_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            task_type_name=project,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'taskType': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_m_weekends(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=7,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_m_weekends_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            task_type_name=project,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=7,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'taskType': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_m_weekends_adjacent(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=True,
            is_adjacent=True,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5 * 7),
                                datetime.min.time())
        expected = [
            {'$match': {'user': user_id, 'end_time': {'$gt': then}}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'},
            }},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_m_weekends_adjacent_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            task_type_name=project,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=True,
            is_adjacent=True,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5 * 7),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'end_time': {'$gt': then},
                'taskType': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_m_days_adjacent(self):
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5),
                                datetime.min.time())
        expected = [
            {'$match': {'user': user_id, 'end_time': {'$gt': then}}},
            {'$project': {
                'day': {'$dayOfMonth': '$end_time'},
                'month': {'$month': '$end_time'},
                'year': {'$year': '$end_time'}}},
            {'$group': {
                '_id': {'day': '$day', 'month': '$month', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))

    def test_m_days_adjacent_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            task_type_name=project,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'end_time': {'$gt': then},
                'taskType': project}},
            {'$project': {
                'day': {'$dayOfMonth': '$end_time'},
                'month': {'$month': '$end_time'},
                'year': {'$year': '$end_time'}}},
            {'$group': {
                '_id': {'day': '$day', 'month': '$month', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build_for(user_id))


class TestMongoQueryExecutor(BaseTest):
    NOW = datetime.now()
    HOUR = timedelta(hours=1)
    DAY = timedelta(days=1)

    def setUp(self):
        super().setUp()

    def tearDown(self):
        WorkSession.drop_collection()
        super().tearDown()

    def test_n_tasks_ok(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)

        WorkSession(user=uid, task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task_two',
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task_three',
                    start_time=self.NOW - self.DAY * 2, end_time=self.NOW) \
            .save()
        WorkSession(user=ObjectId(), task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_fail(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)

        WorkSession(user=uid, task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task_two',
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=ObjectId(), task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)

    def test_n_tasks_project_ok(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False)

        WorkSession(user=uid, task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY * 2, end_time=self.NOW) \
            .save()
        WorkSession(user=ObjectId(), task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_project_fail(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False)

        WorkSession(user=uid, task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY * 2, end_time=self.NOW) \
            .save()
        WorkSession(user=ObjectId(), task=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_m_days_ok(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=21,
            days_number=7,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)

        for i in range(1, 22):
            day_i = self.NOW - self.DAY * (i % 7)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_m_days_project_ok(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False)

        for i in range(1, 22):
            day_i = self.NOW - self.DAY * (i % 7)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type=task_type_name,
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_m_days_more_days(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=21,
            days_number=7,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)

        for i in range(1, 22):
            # tasks are spread across 9 days, which is more
            day_i = self.NOW - self.DAY * (i % 9)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)

    def test_n_tasks_m_days_less_tasks(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=21,
            days_number=7,
            is_weekend=False,
            is_adjacent=False,
            rule_id=100)
        # less tasks
        for i in range(1, 21):
            day_i = self.NOW - self.DAY * (i % 3)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)

    def test_n_tasks_weekends_sun(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(1, 22):
            day_i = (self.NOW - to_sun) - self.DAY * 7
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_weekends_sat(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        to_sat = timedelta(days=(self.NOW.weekday() + 1) % 6)

        for i in range(1, 22):
            day_i = (self.NOW - to_sat) - self.DAY * 7
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_weekends_mon_fail(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=20,
            days_number=0,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        to_mon = timedelta(days=self.NOW.weekday())

        for i in range(1, 22):
            day_i = (self.NOW - to_mon) - self.DAY * 7
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)

    def test_m_weekends(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=7,
            is_weekend=True,
            is_adjacent=False,
            rule_id=100)
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(1, 8):
            # every second Sunday
            day_i = (self.NOW - to_sun) - (self.DAY * 7 * i * 2)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task',
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_weekends_project(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=7,
            is_weekend=True,
            is_adjacent=False)
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(1, 8):
            # every second Sunday
            day_i = (self.NOW - to_sun) - (self.DAY * 7 * i * 2)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type=task_type_name,
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_adjacent_weekends(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=7,
            is_weekend=True,
            is_adjacent=True,
            rule_id=100)
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(0, 8):
            # every second Sunday
            day_i = (self.NOW - to_sun) - (self.DAY * 7 * i)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task',
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_adjacent_weekends_project(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=7,
            is_weekend=True,
            is_adjacent=True)
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(0, 8):
            # every second Sunday
            day_i = (self.NOW - to_sun) - (self.DAY * 7 * i)
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type=task_type_name,
                        start_time=day_i,
                        end_time=day_i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_days_adjacent_ok(self):
        uid = ObjectId()
        rule = Rule(
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)

        for i in range(1, 6):
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task',
                        start_time=self.NOW - self.DAY * i,
                        end_time=self.NOW - self.DAY * i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_days_adjacent_project_ok(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True)

        for i in range(1, 6):
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type=task_type_name,
                        start_time=self.NOW - self.DAY * i,
                        end_time=self.NOW - self.DAY * i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_days_adjacent_project_fail(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id=100,
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True)

        for i in range(1, 6):
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task_%s' % i,
                        start_time=self.NOW - self.DAY * i,
                        end_time=self.NOW - self.DAY * i
                        ).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)
