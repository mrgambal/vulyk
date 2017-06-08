# -*- coding: utf-8 -*-
from bson import ObjectId
from datetime import date, timedelta

from vulyk.blueprints.gamification.core.queries import MongoRuleQueryBuilder
from vulyk.blueprints.gamification.core.rules import Rule, ProjectRule

from ..base import BaseTest


class TestMongoQueryBuilder(BaseTest):
    TASKS = 20
    DAYS = 7
    WEEKEND = True
    ADJACENT = True

    def test_n_tasks(self):
        rule = Rule('', '', '', 0, self.TASKS, 0, False, False, '')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [{'$match': {'user': user_id}}]

        self.assertEqual(expected, builder.build(user_id))

    def test_n_tasks_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            project, '', '', '', 0, self.TASKS, 0, False, False, '')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [{'$match':
                         {'user': user_id,
                          'task_type': project}}]

        self.assertEqual(expected, builder.build(user_id))

    def test_n_tasks_m_days(self):
        rule = Rule('', '', '', 0, self.TASKS, self.DAYS, False, False, '')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = date.today() - timedelta(days=self.DAYS)
        expected = [{'$match':
                         {'user': user_id,
                          'end_date': {'$gt': then}}}]

        self.assertEqual(expected, builder.build(user_id))

    def test_n_tasks_m_days_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            project, '', '', '', 0, self.TASKS, self.DAYS, False, False, '')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = date.today() - timedelta(days=self.DAYS)
        expected = [{'$match':
                         {'user': user_id,
                          'end_date': {'$gt': then},
                          'task_type': project}}]

        self.assertEqual(expected, builder.build(user_id))

    def test_n_tasks_weekends(self):
        rule = Rule('', '', '', 0, self.TASKS, 0, self.WEEKEND, False, '')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id}},
            {'$project': {'dayOfWeek': {'$dayOfWeek': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}}
        ]

        self.assertEqual(expected, builder.build(user_id))

    def test_n_tasks_weekends_project(self):
        project = 'fake_tasks'
        rule = ProjectRule(
            project, '', '', '', 0, self.TASKS, 0, self.WEEKEND, False, '')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'task_type': project}},
            {'$project': {'dayOfWeek': {'$dayOfWeek': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}}
        ]

        self.assertEqual(expected, builder.build(user_id))
