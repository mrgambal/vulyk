# -*- coding: utf-8 -*-
from bson import ObjectId
from datetime import date, timedelta

from vulyk.blueprints.gamification.core.queries import MongoRuleQueryBuilder
from vulyk.blueprints.gamification.core.rules import Rule, ProjectRule

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [{'$match': {'user': user_id}}]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'task_type': project}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = date.today() - timedelta(days=7)
        expected = [
            {'$match': {'user': user_id, 'end_date': {'$gt': then}}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        then = date.today() - timedelta(days=7)
        expected = [
            {'$match': {
                'user': user_id,
                'end_date': {'$gt': then},
                'task_type': project}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'task_type': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        expected = [
            {'$match': {'user': user_id, 'task_type': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = date.today() - timedelta(days=5 * 7)
        expected = [
            {'$match': {'user': user_id, 'end_date': {'$gt': then}}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'},
            }},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = date.today() - timedelta(days=5 * 7)
        expected = [
            {'$match': {
                'user': user_id,
                'end_date': {'$gt': then},
                'task_type': project}},
            {'$project': {
                'dayOfWeek': {'$dayOfWeek': '$end_date'},
                'year': {'$year': '$end_date'},
                'week': {'$week': '$end_date'}}},
            {'$match': {'$or': [{'dayOfWeek': 7}, {'dayOfWeek': 1}]}},
            {'$group': {'_id': {'week': '$week', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = date.today() - timedelta(days=5)
        expected = [
            {'$match': {'user': user_id, 'end_date': {'$gt': then}}},
            {'$project': {
                'day': {'$day': '$end_date'},
                'month': {'$month': '$end_date'},
                'year': {'$year': '$end_date'}}},
            {'$group': {
                '_id': {'day': '$day', 'month': '$month', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build(user_id))

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
            string='')
        user_id = ObjectId()
        builder = MongoRuleQueryBuilder(rule=rule)
        # multiply by week length
        then = date.today() - timedelta(days=5)
        expected = [
            {'$match': {
                'user': user_id,
                'end_date': {'$gt': then},
                'task_type': project}},
            {'$project': {
                'day': {'$day': '$end_date'},
                'month': {'$month': '$end_date'},
                'year': {'$year': '$end_date'}}},
            {'$group': {
                '_id': {'day': '$day', 'month': '$month', 'year': '$year'}}}
        ]

        self.assertEqual(expected, builder.build(user_id))
