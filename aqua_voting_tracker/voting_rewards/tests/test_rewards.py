from decimal import Decimal
from typing import Any, Iterable, List, Mapping, Union
from unittest import TestCase
from unittest.mock import patch

from django.conf import settings

from aqua_voting_tracker.voting_rewards.rewards import get_current_reward


def get_markets(market_keys: Iterable[str]):
    return [
        {
            'account_id': market_key,
            'asset1': f'A{i // 2 + 1}:ISSUER',
            'asset2': f'A{i // 2 + 2}:ISSUER',
        }
        for i, market_key in enumerate(market_keys)
    ]


def get_candidates(votes_value):
    return [
        {
            'market_key': f'market{i + 1}',
            'adjusted_votes_value': value,
        }
        for i, value in enumerate(votes_value)
    ]


def get_stats(candidates):
    return {
        'adjusted_votes_value_sum': sum(candidate['adjusted_votes_value'] for candidate in candidates),
    }


@patch('aqua_voting_tracker.voting_rewards.rewards.get_market_pairs', new=get_markets)
class GetCurrentRewardTestCase(TestCase):
    def assert_rewards(self, rewards: List[Mapping[str, Any]]):
        total_reward = sum(reward['reward_value'] for reward in rewards)
        self.assertLessEqual(total_reward, settings.TOTAL_REWARD_VALUE)
        self.assertAlmostEqual(
            total_reward,
            settings.TOTAL_REWARD_VALUE,
            delta=5,
        )
        self.assertTrue(all(reward['reward_value'] == reward['amm_reward_value'] + reward['sdex_reward_value']
                            for reward in rewards))

        self.assertAlmostEqual(
            sum(float(reward['share']) for reward in rewards),
            1,
            delta=0.0001,
        )
        self.assertTrue(all(reward['share'] <= settings.REWARD_MAX_SHARE for reward in rewards))

        prev_reward = rewards[0]
        for reward in rewards[1:]:
            if prev_reward['share'] < settings.REWARD_MAX_SHARE:
                votes_ratio = float(prev_reward['votes_value']) / float(reward['votes_value'])
                self.assertAlmostEqual(float(prev_reward['share']) / float(reward['share']),
                                       votes_ratio, delta=0.01)
                self.assertAlmostEqual(float(prev_reward['reward_value']) / float(reward['reward_value']),
                                       votes_ratio, delta=0.01)
            prev_reward = reward

    def assert_shares(self, rewards: List[Mapping[str, Any]], shares: List[Union[Decimal, str]]):
        self.assertListEqual(
            [reward['share'] for reward in rewards],
            [Decimal(share) for share in shares],
        )

    def test_common(self):
        candidates = get_candidates([95, 90, 85, 80, 75, 70, 65, 60, 55, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10])
        stats = get_stats(candidates)

        with patch('aqua_voting_tracker.voting_rewards.rewards.get_voting_rewards_candidate', new=lambda: candidates):
            with patch('aqua_voting_tracker.voting_rewards.rewards.get_voting_stats', new=lambda: stats):
                rewards = get_current_reward()

        self.assert_rewards(rewards)
        self.assert_shares(rewards, [
            '0.095', '0.09', '0.085', '0.08', '0.075', '0.07', '0.065', '0.06', '0.055', '0.055',
            '0.05', '0.045', '0.04', '0.035', '0.03', '0.025', '0.02', '0.015', '0.01',
        ])

    def test_cut_to_limit1(self):
        candidates = get_candidates([50, 50, 50, 50, 30, 30, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 5, 5, 5, 5])
        stats = get_stats(candidates)

        with patch('aqua_voting_tracker.voting_rewards.rewards.get_voting_rewards_candidate', new=lambda: candidates):
            with patch('aqua_voting_tracker.voting_rewards.rewards.get_voting_stats', new=lambda: stats):
                rewards = get_current_reward()

        self.assert_rewards(rewards)
        self.assert_shares(rewards, [
            '0.1', '0.1', '0.1', '0.1', '0.09', '0.09', '0.06', '0.06', '0.03', '0.03', '0.03',
            '0.03', '0.03', '0.03', '0.03', '0.03', '0.015', '0.015', '0.015', '0.015',
        ])

    def test_cut_to_limit2(self):
        candidates = get_candidates([50, 50, 50, 50, 35, 30, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 5, 5, 5])
        stats = get_stats(candidates)

        with patch('aqua_voting_tracker.voting_rewards.rewards.get_voting_rewards_candidate', new=lambda: candidates):
            with patch('aqua_voting_tracker.voting_rewards.rewards.get_voting_stats', new=lambda: stats):
                rewards = get_current_reward()

        self.assert_rewards(rewards)
        self.assert_shares(rewards, [
            '0.1', '0.1', '0.1', '0.1', '0.1', '0.0909', '0.0606', '0.0606', '0.0303', '0.0303',
            '0.0303', '0.0303', '0.0303', '0.0303', '0.0303', '0.0303', '0.0152', '0.0152', '0.0152',
        ])
