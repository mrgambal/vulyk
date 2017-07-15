# -*- coding: utf-8 -*-
"""
test_state_models
"""
from datetime import datetime, timedelta
from decimal import Decimal

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
    TIMESTAMP_NEXT = TIMESTAMP + timedelta(seconds=1)
    USER = None

    def setUp(self):
        super().setUp()

        Group.objects.create(
            description='test', id='default', allowed_types=[self.TASK_TYPE])
        self.USER = User(username='user0', email='user0@email.com').save()

    def tearDown(self):
        super().tearDown()

        User.objects.delete()
        Group.objects.delete()

        RuleModel.objects.delete()
        UserStateModel.objects.delete()

    def test_rookie_ok(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_level_ok(self):
        state = UserState(
            user=self.USER,
            level=20,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_points_ok(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(20),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
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
            points=Decimal(),
            actual_coins=Decimal(50),
            potential_coins=Decimal(60),
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
            points=Decimal(5000),
            actual_coins=Decimal(3240),
            potential_coins=Decimal(4000),
            achievements=[rule_model],
            last_changed=self.TIMESTAMP
        )
        UserStateModel.from_state(state).save()
        state2 = UserStateModel.objects.get(
            user=self.USER, last_changed=self.TIMESTAMP).to_state()

        self.assertEqual(state, state2,
                         'State was not saved and restored just fine')

    def test_usm_update_state_points(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        diff = UserState(
            user=self.USER,
            level=0,
            points=Decimal(10),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        new_state = state_model.reload().to_state()

        self.assertEqual(diff, new_state)
        self.assertEqual(diff.last_changed, new_state.last_changed)

    def test_usm_update_state_level(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        diff = UserState(
            user=self.USER,
            level=1,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        new_state = state_model.reload().to_state()

        self.assertEqual(diff, new_state)

    def test_usm_update_state_actual_coins(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        diff = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(200),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        new_state = state_model.reload().to_state()

        self.assertEqual(diff, new_state)

    def test_usm_update_state_potential_coins(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        diff = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(300),
            achievements=[],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        new_state = state_model.reload().to_state()

        self.assertEqual(diff, new_state)

    def test_usm_update_state_achievements(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
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
        RuleModel.from_rule(rule).save()
        diff = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[rule],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        new_state = state_model.reload().to_state()

        self.assertEqual(diff, new_state)

    def test_usm_update_state_all_together(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
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
        RuleModel.from_rule(rule).save()
        diff = UserState(
            user=self.USER,
            level=80,
            points=Decimal(200),
            actual_coins=Decimal(20),
            potential_coins=Decimal(100),
            achievements=[rule],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        new_state = state_model.reload().to_state()

        self.assertEqual(diff, new_state)

    def test_usm_update_state_twice(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        rule = Rule(
            badge='',
            name='Rule 1',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=100)
        RuleModel.from_rule(rule).save()
        rule_two = Rule(
            badge='',
            name='Rule 2',
            description='',
            bonus=0,
            tasks_number=0,
            days_number=5,
            is_weekend=False,
            is_adjacent=True,
            rule_id=200)
        RuleModel.from_rule(rule_two).save()
        diff = UserState(
            user=self.USER,
            level=80,
            points=Decimal(200),
            actual_coins=Decimal(20),
            potential_coins=Decimal(100),
            achievements=[rule],
            last_changed=self.TIMESTAMP_NEXT)
        diff_two = UserState(
            user=self.USER,
            level=81,
            points=Decimal(50),
            actual_coins=Decimal(200),
            potential_coins=Decimal(100),
            # just by some mistake we passed `rule` twice
            achievements=[rule, rule_two],
            last_changed=self.TIMESTAMP_NEXT)

        UserStateModel.update_state(diff=diff)
        UserStateModel.update_state(diff=diff_two)
        new_state = state_model.reload().to_state()

        self.assertEqual(new_state.points, diff.points + diff_two.points)
        self.assertEqual(new_state.level, diff_two.level)
        self.assertEqual(new_state.actual_coins,
                         diff.actual_coins + diff_two.actual_coins)
        self.assertEqual(new_state.potential_coins,
                         diff.potential_coins + diff_two.potential_coins)
        self.assertSetEqual(set(new_state.achievements.keys()), {200, 100})
        self.assertEqual(new_state.last_changed, diff_two.last_changed)

    def test_rookie_to_dict(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(),
            potential_coins=Decimal(),
            achievements=[],
            last_changed=self.TIMESTAMP)
        expected = {
            'user': self.USER.username,
            'level': 0,
            'points': 0,
            'actual_coins': 0,
            'potential_coins': 0,
            'achievements': [],
            'last_changed': self.TIMESTAMP.strftime("%d.%m.%Y %H:%M:%S")
        }

        self.assertDictEqual(expected, state.to_dict())

    def test_everything_to_dict(self):
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
        state = UserState(
            user=self.USER,
            level=80,
            points=Decimal(200),
            actual_coins=Decimal(20),
            potential_coins=Decimal(100),
            achievements=[rule],
            last_changed=self.TIMESTAMP)
        expected = {
            'user': self.USER.username,
            'level': 80,
            'points': 200,
            'actual_coins': 20,
            'potential_coins': 100,
            'achievements': [rule.to_dict()],
            'last_changed': self.TIMESTAMP.strftime("%d.%m.%Y %H:%M:%S")
        }

        self.assertDictEqual(expected, state.to_dict())
