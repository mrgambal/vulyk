# -*- coding: utf-8 -*-
"""
test_state_models
"""
from datetime import datetime, timedelta
from decimal import Decimal
from operator import attrgetter

from vulyk.blueprints.gamification.core.rules import Rule
from vulyk.blueprints.gamification.core.state import UserState
from vulyk.blueprints.gamification.models.rules import RuleModel
from vulyk.blueprints.gamification.models.state import (
    UserStateModel, StateSortingKeys)
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

        self.assertDictEqual(expected, state.to_dict(),
                             'Wrong state to dict conversion')

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

        self.assertDictEqual(expected, state.to_dict(),
                             'Wrong state to dict conversion')

    def test_create_if_not_exists(self):
        state = UserStateModel.get_or_create_by_user(self.USER)

        self.assertEqual(state.user.username, self.USER.username,
                         'Wrong username for newly created state')
        self.assertEqual(state.level, 0,
                         'Wrong level for newly created state')
        self.assertEqual(state.points, Decimal(),
                         'Wrong points for newly created state')
        self.assertEqual(state.actual_coins, Decimal(),
                         'Wrong actual coins for newly created state')
        self.assertEqual(state.potential_coins, Decimal(),
                         'Wrong potential coins for newly created state')
        self.assertEqual(state.achievements, {},
                         'Wrong achievements set for newly created state')

    def test_top_correct_limit(self):
        [
            UserStateModel.from_state(
                UserState(
                    user=User(
                        username='user%s' % i,
                        email='user%s@email.com' % i).save(),
                    level=i,
                    points=Decimal(200),
                    actual_coins=Decimal(20),
                    potential_coins=Decimal(100),
                    achievements=[],
                    last_changed=self.TIMESTAMP
                )
            ).save() for i in range(5)
        ]
        sorting = StateSortingKeys.LEVEL

        for i in range(1, 5):
            self.assertEqual(
                len(list((UserStateModel.get_top_users(i, sorting)))), i,
                'Limiting was not applied correctly: %s items' % i)

    def test_top_correct_sorting(self):
        [
            UserStateModel.from_state(
                UserState(
                    user=User(
                        username='user%s' % i,
                        email='user%s@email.com' % i).save(),
                    level=i,
                    points=Decimal(i * 20),
                    actual_coins=Decimal(100 - i * 20),
                    potential_coins=Decimal(100 - i if i % 2 else 100 + i),
                    achievements=[],
                    last_changed=self.TIMESTAMP
                )
            ).save() for i in range(5)
        ]

        for item in StateSortingKeys:
            key = item.name.lower()
            result = UserStateModel.get_top_users(5, item)
            properties = list(map(attrgetter(key), result))

            self.assertSequenceEqual(
                properties, sorted(properties, reverse=True),
                'Sorting was not applied correctly: %s' % key)

    def test_withdraw_positive(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(100),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal(99))
        state_model.reload()

        self.assertTrue(result)
        self.assertEqual(state_model.actual_coins, Decimal(1))
        self.assertEqual(state_model.potential_coins, Decimal(500))

    def test_withdraw_positive_point(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(100),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal('99.5'))
        state_model.reload()

        self.assertTrue(result)
        self.assertEqual(state_model.actual_coins, Decimal('0.5'))
        self.assertEqual(state_model.potential_coins, Decimal(500))

    def test_withdraw_negative(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(100),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal(-99))
        state_model.reload()

        self.assertTrue(result)
        self.assertEqual(state_model.actual_coins, Decimal(1))
        self.assertEqual(state_model.potential_coins, Decimal(500))

    def test_withdraw_negative_point(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(100),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal('-99.5'))
        state_model.reload()

        self.assertTrue(result)
        self.assertEqual(state_model.actual_coins, Decimal('0.5'))
        self.assertEqual(state_model.potential_coins, Decimal(500))

    def test_withdraw_no_money_positive(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(80),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal(99))
        state_model.reload()

        self.assertFalse(result)
        self.assertEqual(state_model.actual_coins, Decimal(80))
        self.assertEqual(state_model.potential_coins, Decimal(500))

    def test_withdraw_no_money_positive_point(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(80),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal('99.5'))
        state_model.reload()

        self.assertFalse(result)
        self.assertEqual(state_model.actual_coins, Decimal(80))
        self.assertEqual(state_model.potential_coins, Decimal(500))

    def test_withdraw_no_money_negative(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(80),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal(-99))
        state_model.reload()

        self.assertEqual(state_model.actual_coins, Decimal(80))
        self.assertEqual(state_model.potential_coins, Decimal(500))
        self.assertFalse(result)

    def test_withdraw_no_money_negative_point(self):
        state = UserState(
            user=self.USER,
            level=0,
            points=Decimal(),
            actual_coins=Decimal(80),
            potential_coins=Decimal(500),
            achievements=[],
            last_changed=self.TIMESTAMP)
        state_model = UserStateModel.from_state(state).save()
        result = UserStateModel.withdraw(self.USER, Decimal('-98.5'))
        state_model.reload()

        self.assertEqual(state_model.actual_coins, Decimal(80))
        self.assertEqual(state_model.potential_coins, Decimal(500))
        self.assertFalse(result)
