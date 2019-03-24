# -*- coding: utf-8 -*-
"""
test_query_builders
"""
import unittest
from datetime import date, datetime, timedelta

from bson import ObjectId

from vulyk.blueprints.gamification.core.queries import (
    MongoRuleExecutor,
    MongoRuleQueryBuilder)
from vulyk.blueprints.gamification.core.rules import Rule, ProjectRule
from vulyk.blueprints.gamification.models.rules import (
    RuleModel, AllRules, ProjectAndFreeRules, StrictProjectRules)
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'answer': {'$exists': True}}},
            {"$count": "achieved"}
        ]

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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {
                'user': user_id,
                'taskType': project,
                'answer': {'$exists': True}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = datetime.combine(date.today() - timedelta(days=7),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'answer': {'$exists': True},
                'end_time': {'$gt': then}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = datetime.combine(date.today() - timedelta(days=7),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'answer': {'$exists': True},
                'end_time': {'$gt': then},
                'taskType': project}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'answer': {'$exists': True}}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'taskType': project, 'answer': {'$exists': True}}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'answer': {'$exists': True}}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'answer': {'$exists': True}, 'taskType': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5 * 7),
                                datetime.min.time())
        expected = [
            {'$match': {'user': user_id, 'answer': {'$exists': True}, 'end_time': {'$gt': then}}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'},
            }},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5 * 7),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'answer': {'$exists': True},
                'end_time': {'$gt': then},
                'taskType': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_time'},
                'year': {'$year': '$end_time'},
                'week': {'$week': '$end_time'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5),
                                datetime.min.time())
        expected = [
            {'$match': {'user': user_id, 'answer': {'$exists': True}, 'end_time': {'$gt': then}}},
            {'$project': {
                'day': {'$dayOfMonth': '$end_time'},
                'month': {'$month': '$end_time'},
                'year': {'$year': '$end_time'}}},
            {'$group': {
                '_id': {'day': '$day', 'month': '$month', 'year': '$year'}}},
            {"$count": "achieved"}
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
            rule_id='100')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = datetime.combine(date.today() - timedelta(days=5),
                                datetime.min.time())
        expected = [
            {'$match': {
                'user': user_id,
                'answer': {'$exists': True},
                'end_time': {'$gt': then},
                'taskType': project}},
            {'$project': {
                'day': {'$dayOfMonth': '$end_time'},
                'month': {'$month': '$end_time'},
                'year': {'$year': '$end_time'}}},
            {'$group': {
                '_id': {'day': '$day', 'month': '$month', 'year': '$year'}}},
            {"$count": "achieved"}
        ]

        self.assertEqual(expected, builder.build_for(user_id))


class TestMongoQueryExecutor(BaseTest):
    NOW = datetime.now()
    HOUR = timedelta(hours=1)
    DAY = timedelta(days=1)

    def tearDown(self):
        WorkSession.objects.delete()
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
            rule_id='100')

        WorkSession(user=uid, task=ObjectId(), task_type='fake_task',
                    answer=ObjectId(),
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task_two',
                    answer=ObjectId(),
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task_three',
                    answer=ObjectId(),
                    start_time=self.NOW - self.DAY * 2, end_time=self.NOW) \
            .save()
        WorkSession(user=ObjectId(), task=ObjectId(), task_type='fake_task',
                    answer=ObjectId(),
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
            rule_id='100')

        WorkSession(user=uid, task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task_two',
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=ObjectId(), task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)

    def test_n_tasks_unclosed_session_fail(self):
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
            rule_id='100')

        WorkSession(user=uid, task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), task_type='fake_task',
                    start_time=self.NOW - self.DAY).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)

    def test_n_tasks_project_ok(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False)

        WorkSession(user=uid, task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY * 2, end_time=self.NOW) \
            .save()
        WorkSession(user=ObjectId(), task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_project_fail(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
            task_type_name=task_type_name,
            badge='',
            name='',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False)

        WorkSession(user=uid, task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.HOUR, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY, end_time=self.NOW).save()
        WorkSession(user=uid, task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
                    start_time=self.NOW - self.DAY * 2, end_time=self.NOW) \
            .save()
        WorkSession(user=ObjectId(), task=ObjectId(), answer=ObjectId(), task_type=task_type_name,
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
            rule_id='100')

        for i in range(1, 22):
            day_i = self.NOW - self.DAY * (i % 7)
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_n_tasks_m_days_project_ok(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
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
                        answer=ObjectId(),
                        task_type=task_type_name,
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')

        for i in range(1, 22):
            # tasks are spread across 9 days, which is more
            day_i = self.NOW - self.DAY * (i % 9)
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')
        # less tasks
        for i in range(1, 21):
            day_i = self.NOW - self.DAY * (i % 3)
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(1, 22):
            day_i = (self.NOW - to_sun) - self.DAY * 7
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')
        to_sat = timedelta(days=(self.NOW.weekday() + 1) % 6)

        for i in range(1, 22):
            day_i = (self.NOW - to_sat) - self.DAY * 7
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')
        to_mon = timedelta(days=self.NOW.weekday())

        for i in range(1, 22):
            day_i = (self.NOW - to_mon) - self.DAY * 7
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task_%s' % (i % 3),
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(1, 8):
            # every second Sunday
            day_i = (self.NOW - to_sun) - (self.DAY * 7 * i * 2)
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task',
                        start_time=day_i,
                        end_time=day_i).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_weekends_project(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
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
                        answer=ObjectId(),
                        task_type=task_type_name,
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')
        to_sun = timedelta(days=(self.NOW.weekday() + 1) % 7)

        for i in range(0, 8):
            # every second Sunday
            day_i = (self.NOW - to_sun) - (self.DAY * 7 * i)
            WorkSession(user=uid,
                        task=ObjectId(),
                        answer=ObjectId(),
                        task_type='fake_task',
                        start_time=day_i,
                        end_time=day_i).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_adjacent_weekends_project(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
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
                        answer=ObjectId(),
                        task_type=task_type_name,
                        start_time=day_i,
                        end_time=day_i).save()

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
            rule_id='100')

        for i in range(1, 6):
            WorkSession(user=uid,
                        task=ObjectId(),
                        task_type='fake_task',
                        answer=ObjectId(),
                        start_time=self.NOW - self.DAY * i,
                        end_time=self.NOW - self.DAY * i).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_days_adjacent_project_ok(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
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
                        answer=ObjectId(),
                        task_type=task_type_name,
                        start_time=self.NOW - self.DAY * i,
                        end_time=self.NOW - self.DAY * i).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertTrue(result)

    def test_m_days_adjacent_project_fail(self):
        uid = ObjectId()
        task_type_name = 'fake_task'
        rule = ProjectRule(
            rule_id='100',
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
                        answer=ObjectId(),
                        task_type='fake_task_%s' % i,
                        start_time=self.NOW - self.DAY * i,
                        end_time=self.NOW - self.DAY * i).save()

        result = MongoRuleExecutor.achieved(
            user_id=uid, rule=rule, collection=WorkSession.objects)

        self.assertFalse(result)


class TestRuleModel(BaseTest):
    RULES = [
        Rule(
            badge='',
            name='rule_1',
            description='',
            bonus=0,
            tasks_number=3,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id='100'),
        Rule(
            badge='',
            name='rule_2',
            description='',
            bonus=10,
            tasks_number=30,
            days_number=0,
            is_weekend=False,
            is_adjacent=False,
            rule_id='200'),
        ProjectRule(
            rule_id='300',
            task_type_name='project_1',
            badge='',
            name='rule_3',
            description='',
            bonus=0,
            tasks_number=40,
            days_number=0,
            is_weekend=False,
            is_adjacent=False),
        ProjectRule(
            rule_id='400',
            task_type_name='project_2',
            badge='',
            name='rule_4',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True),
    ]

    def setUp(self):
        super().setUp()

        for rule in self.RULES:
            RuleModel.from_rule(rule).save()

    def tearDown(self):
        RuleModel.objects.delete()

        super().tearDown()

    def test_everything_ok(self):
        self.assertEqual(
            len(self.RULES),
            len(list(RuleModel.get_actual_rules([], AllRules(), False)))
        )

    def test_everything_project_1(self):
        rules = list(RuleModel.get_actual_rules(
            [], ProjectAndFreeRules('project_1'), False))

        self.assertEqual(3, len(rules))
        self.assertTrue(any(r.id == '300' for r in rules))
        self.assertTrue(all(r.id != '400' for r in rules))

    def test_everything_project_2(self):
        rules = list(RuleModel.get_actual_rules(
            [], ProjectAndFreeRules('project_2'), False))

        self.assertEqual(3, len(rules))
        self.assertTrue(any(r.id == '400' for r in rules))
        self.assertTrue(all(r.id != '300' for r in rules))

    def test_everything_and_weekend(self):
        RuleModel.from_rule(
            Rule(
                badge='',
                name='rule_5',
                description='',
                bonus=0,
                tasks_number=3,
                days_number=0,
                is_weekend=True,
                is_adjacent=False,
                rule_id='500')).save()
        rules = list(RuleModel.get_actual_rules([], AllRules(), True))
        rules_no_weekend = list(
            RuleModel.get_actual_rules([], AllRules(), False))

        self.assertEqual(5, len(rules))
        self.assertTrue(any(r.id == '500' for r in rules))

        self.assertEqual(4, len(rules_no_weekend))
        self.assertTrue(all(r.id != '500' for r in rules_no_weekend))

    def test_exclude_ids(self):
        ids = ['100', '200']
        rules = list(RuleModel.get_actual_rules(ids, AllRules(), False))

        self.assertEqual(2, len(rules))
        self.assertTrue(all(r.id not in ids for r in rules))

    def test_exclude_ids_project(self):
        ids = ['100', '200']
        rules = list(RuleModel.get_actual_rules(
            ids, ProjectAndFreeRules('project_1'), False))

        self.assertEqual(1, len(rules))
        self.assertTrue(rules[0].id, '300')

    def test_exclude_ids_weekend(self):
        RuleModel.from_rule(
            Rule(
                badge='',
                name='rule_5',
                description='',
                bonus=0,
                tasks_number=3,
                days_number=0,
                is_weekend=True,
                is_adjacent=False,
                rule_id='500')).save()
        ids = ['100', '200']
        rules = list(RuleModel.get_actual_rules(ids, AllRules(), True))

        self.assertEqual(3, len(rules))
        self.assertTrue(any(r.id == '500' for r in rules))

    def test_exclude_ids_project_weekend(self):
        RuleModel.from_rule(
            Rule(
                badge='',
                name='rule_5',
                description='',
                bonus=0,
                tasks_number=3,
                days_number=0,
                is_weekend=True,
                is_adjacent=False,
                rule_id='500')).save()
        RuleModel.from_rule(
            ProjectRule(
                task_type_name='project_3',
                badge='',
                name='rule_6',
                description='',
                bonus=0,
                tasks_number=3,
                days_number=0,
                is_weekend=True,
                is_adjacent=False,
                rule_id='600')).save()
        ids = ['100', '500']
        rules = list(RuleModel.get_actual_rules(
            ids, ProjectAndFreeRules('project_3'), True))

        self.assertEqual(2, len(rules))
        self.assertTrue(all(r.id in ['200', '600'] for r in rules))
        self.assertTrue(all(r.id != '500' for r in rules))

    def test_exclude_ids_strict_project_weekend(self):
        RuleModel.from_rule(
            Rule(
                badge='',
                name='rule_5',
                description='',
                bonus=0,
                tasks_number=3,
                days_number=0,
                is_weekend=True,
                is_adjacent=False,
                rule_id='500')).save()
        RuleModel.from_rule(
            ProjectRule(
                task_type_name='project_3',
                badge='',
                name='rule_6',
                description='',
                bonus=0,
                tasks_number=3,
                days_number=0,
                is_weekend=True,
                is_adjacent=False,
                rule_id='600')).save()
        ids = ['100', '500']
        rules = list(RuleModel.get_actual_rules(
            ids, StrictProjectRules('project_3'), True))

        self.assertEqual(1, len(rules))
        self.assertTrue(rules[0].id, '600')


if __name__ == '__main__':
    unittest.main()
