# -*- coding: utf-8 -*-
"""
test_state_models
"""
from datetime import datetime

from vulyk.blueprints.gamification.core.rules import Rule
from vulyk.blueprints.gamification.core.state import UserState
from vulyk.blueprints.gamification.models.rules import RuleModel
from vulyk.blueprints.gamification.models.state import UserStateModel
from vulyk.models.user import Group, User

from ..base import BaseTest
from ..fixtures import FakeType


class TestStateModels(BaseTest):
    TASK_TYPE = FakeType.type_name
    TIMESTAMP = datetime.now()
    USER = None

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])
        self.USER = User(username='user0', email='user0@email.com').save()

    def tearDown(self):
        super().tearDown()

        User.drop_collection()
        Group.drop_collection()

        RuleModel.drop_collection()
        UserStateModel.drop_collection()

    def test_rookie_ok(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=0,
            actual_coins=0,
            potential_coins=0,
            achievements=[],
            last_changed=self.TIMESTAMP
        )
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_level_ok(self):
        state = UserState(
            user=self.USER,
            level=20,
            points=0,
            actual_coins=0,
            potential_coins=0,
            achievements=[],
            last_changed=self.TIMESTAMP
        )
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_points_ok(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=20,
            actual_coins=0,
            potential_coins=0,
            achievements=[],
            last_changed=self.TIMESTAMP
        )
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_coins_ok(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=0,
            actual_coins=50,
            potential_coins=60,
            achievements=[],
            last_changed=self.TIMESTAMP
        )
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_badges_ok(self):
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
        rule_model = RuleModel.from_rule(rule).save()
        state = UserState(
            user=self.USER,
            level=20,
            points=5000,
            actual_coins=3240,
            potential_coins=4000,
            achievements=[rule_model],
            last_changed=self.TIMESTAMP
        )
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')
