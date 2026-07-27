from decimal import Decimal
from typing import Iterable, List, Union
from unittest import TestCase
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings

from aqua_voting_tracker.voting_rewards.services.rewards.base import MarketReward
from aqua_voting_tracker.voting_rewards.services.rewards.v1 import RewardsV1Calculator


# Soroban (non-SAC) tokens come from marketkeys-tracker as a bare contract id
SOROBAN_CONTRACT = 'C' + 'A' * 55


def get_markets(market_keys: Iterable[str]):
    return [
        {
            'account_id': market_key,
            'asset1': f'A{i // 2 + 1}:ISSUER',
            'asset2': f'A{i // 2 + 2}:ISSUER',
            'whitelisted_for_rewards': True,
        }
        for i, market_key in enumerate(market_keys)
    ]


def make_get_markets(whitelist_flags: List[bool]):
    def _builder(market_keys: Iterable[str]):
        keys = list(market_keys)
        return [
            {
                'account_id': market_key,
                'asset1': f'A{i // 2 + 1}:ISSUER',
                'asset2': f'A{i // 2 + 2}:ISSUER',
                'whitelisted_for_rewards': whitelist_flags[i] if i < len(whitelist_flags) else False,
            }
            for i, market_key in enumerate(keys)
        ]
    return _builder


def make_get_markets_with_soroban(soroban_indices: set):
    def _builder(market_keys: Iterable[str]):
        keys = list(market_keys)
        return [
            {
                'account_id': market_key,
                'asset1': SOROBAN_CONTRACT if i in soroban_indices else f'A{i // 2 + 1}:ISSUER',
                'asset2': f'A{i // 2 + 2}:ISSUER',
                'whitelisted_for_rewards': True,
            }
            for i, market_key in enumerate(keys)
        ]
    return _builder


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


@patch('aqua_voting_tracker.voting_rewards.services.rewards.base.get_market_pairs', new=get_markets)
class GetCurrentRewardTestCase(TestCase):
    get_candidates_patch = 'aqua_voting_tracker.voting_rewards.services.rewards.base.get_voting_rewards_candidate'
    get_stats_patch = 'aqua_voting_tracker.voting_rewards.services.rewards.base.get_voting_stats'

    def assert_rewards(self, rewards: List[MarketReward]):
        total_reward = sum(reward.reward_value for reward in rewards)
        # Cap-only, no redistribution: each market earns share * TOTAL_REWARDS
        # against the FULL denominator, clamped at the cap. The dispersed total
        # is <= TOTAL_REWARDS (short by the capped excess and any dropped share);
        # it is no longer normalized back up to TOTAL_REWARDS.
        self.assertLessEqual(total_reward, settings.TOTAL_REWARD_VALUE)
        self.assertTrue(all(reward.reward_value == reward.amm_reward_value + reward.sdex_reward_value
                            for reward in rewards))

        self.assertTrue(all(reward.share <= settings.REWARD_MAX_SHARE for reward in rewards))

        prev_reward = rewards[0]
        for reward in rewards[1:]:
            if prev_reward.share < settings.REWARD_MAX_SHARE:
                votes_ratio = float(prev_reward.votes_value) / float(reward.votes_value)
                self.assertAlmostEqual(float(prev_reward.share) / float(reward.share),
                                       votes_ratio, delta=0.01)
                self.assertAlmostEqual(float(prev_reward.reward_value) / float(reward.reward_value),
                                       votes_ratio, delta=0.01)
            prev_reward = reward

    def assert_shares(self, rewards: List[MarketReward], shares: List[Union[Decimal, str]]):
        self.assertListEqual(
            [reward.share for reward in rewards],
            [Decimal(share) for share in shares],
        )

    def test_common(self):
        candidates = get_candidates([95, 90, 85, 80, 75, 70, 65, 60, 55, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10])
        stats = get_stats(candidates)

        with patch(self.get_candidates_patch, new=lambda x: candidates):
            with patch(self.get_stats_patch, new=lambda: stats):
                rewards = RewardsV1Calculator().run()

        self.assert_rewards(rewards)
        self.assert_shares(rewards, [
            '0.095', '0.09', '0.085', '0.08', '0.075', '0.07', '0.065', '0.06', '0.055', '0.055',
            '0.05', '0.045', '0.04', '0.035', '0.03', '0.025', '0.02', '0.015', '0.01',
        ])

    def test_cut_to_limit1(self):
        # denominator = sum = 400. Cap-only, no redistribution: markets over the
        # cap clamp to 0.1 and the excess is dropped (not spread to the rest), so
        # every below-cap market keeps its raw votes/400 share.
        candidates = get_candidates([50, 50, 50, 50, 30, 30, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 5, 5, 5, 5])
        stats = get_stats(candidates)

        with patch(self.get_candidates_patch, new=lambda x: candidates):
            with patch(self.get_stats_patch, new=lambda: stats):
                rewards = RewardsV1Calculator().run()

        self.assert_rewards(rewards)
        self.assert_shares(rewards, [
            '0.1', '0.1', '0.1', '0.1', '0.075', '0.075', '0.05', '0.05', '0.025', '0.025', '0.025',
            '0.025', '0.025', '0.025', '0.025', '0.025', '0.0125', '0.0125', '0.0125', '0.0125',
        ])

    def test_cut_to_limit2(self):
        # denominator = sum = 400. Four markets clamp to the 0.1 cap; the rest keep
        # their raw votes/400 share. No redistribution of the capped excess.
        candidates = get_candidates([50, 50, 50, 50, 35, 30, 20, 20, 10, 10, 10, 10, 10, 10, 10, 10, 5, 5, 5])
        stats = get_stats(candidates)

        with patch(self.get_candidates_patch, new=lambda x: candidates):
            with patch(self.get_stats_patch, new=lambda: stats):
                rewards = RewardsV1Calculator().run()

        self.assert_rewards(rewards)
        self.assert_shares(rewards, [
            '0.1', '0.1', '0.1', '0.1', '0.0875', '0.075', '0.05', '0.05', '0.025', '0.025',
            '0.025', '0.025', '0.025', '0.025', '0.025', '0.025', '0.0125', '0.0125', '0.0125',
        ])

    def test_whitelist_survivors_keep_raw_share(self):
        # Cap-only, no redistribution, FULL denominator. filter_eligible drops the
        # non-whitelisted markets, but the dropped votes stay in the denominator
        # (sum of all candidates = 1000), so survivors do NOT lift to the cap —
        # each keeps its raw votes/1000 share. None of the five survivors reach
        # 0.1, so total = 0.425 * TOTAL_REWARDS, well below TOTAL_REWARDS.
        candidates = get_candidates([95, 90, 85, 80, 75, 70, 65, 60, 55, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10])
        stats = get_stats(candidates)

        whitelist_flags = [True] * 5 + [False] * 14

        with patch(self.get_candidates_patch, new=lambda x: candidates):
            with patch(self.get_stats_patch, new=lambda: stats):
                with patch(
                    'aqua_voting_tracker.voting_rewards.services.rewards.base.get_market_pairs',
                    new=make_get_markets(whitelist_flags),
                ):
                    rewards = RewardsV1Calculator().run()

        self.assert_rewards(rewards)
        self.assertEqual(len(rewards), 5)

        # Survivors votes = [95, 90, 85, 80, 75], full denominator = 1000.
        # Raw shares stay below the cap; no lift, no redistribution.
        self.assert_shares(rewards, ['0.095', '0.09', '0.085', '0.08', '0.075'])

        # Total = 0.425 * 7M = 2,975,000. The other 57.5% of votes are not emitted.
        total_reward = sum(reward.reward_value for reward in rewards)
        self.assertAlmostEqual(
            total_reward,
            settings.TOTAL_REWARD_VALUE * Decimal('0.425'),
            delta=5,
        )
        self.assertLessEqual(total_reward, settings.TOTAL_REWARD_VALUE)

    def test_whitelist_cap_then_drop_no_redistribute(self):
        # Cap-only, FULL denominator (= 1000). The dominant market is dropped as
        # non-whitelisted; its share is simply not emitted and is NOT spread to
        # survivors. The whitelisted 200-vote market clamps to the 0.1 cap; the
        # four 50-vote markets keep raw 0.05. Excess above the cap is dropped.
        # Votes [600, 200, 50, 50, 50, 50]; first (600) not whitelisted.
        candidates = get_candidates([600, 200, 50, 50, 50, 50])
        stats = get_stats(candidates)

        whitelist_flags = [False, True, True, True, True, True]

        with patch(self.get_candidates_patch, new=lambda x: candidates):
            with patch(self.get_stats_patch, new=lambda: stats):
                with patch(
                    'aqua_voting_tracker.voting_rewards.services.rewards.base.get_market_pairs',
                    new=make_get_markets(whitelist_flags),
                ):
                    rewards = RewardsV1Calculator().run()

        self.assert_rewards(rewards)
        self.assertEqual(len(rewards), 5)

        # m2 = 200/1000 = 0.2 -> clamp 0.1; m3..m6 = 50/1000 = 0.05 (unchanged).
        self.assert_shares(rewards, ['0.1', '0.05', '0.05', '0.05', '0.05'])

        # Total = (0.1 + 4 * 0.05) * 7M = 0.3 * 7M = 2,100,000. m1's 0.6 (capped to
        # 0.1) and m2's capped excess (0.1) are both dropped, not redistributed.
        total_reward = sum(reward.reward_value for reward in rewards)
        self.assertAlmostEqual(
            total_reward,
            settings.TOTAL_REWARD_VALUE * Decimal('0.3'),
            delta=5,
        )

        # Per-pair reward never exceeds the 700k cap.
        self.assertTrue(all(
            reward.reward_value <= settings.REWARD_MAX_SHARE * settings.TOTAL_REWARD_VALUE
            for reward in rewards
        ))

    def test_sdex_amm_distribution_classic_vs_soroban(self):
        # Classic pairs split the reward between SDEX and AMM by the
        # SDEX_SHARE:AMM_SHARE settings ratio; soroban (non-SAC) pairs have no
        # classic SDEX/AMM markets, so their whole reward goes to the soroban
        # AMM (sdex_reward_value = 0).
        candidates = get_candidates([60, 40])
        stats = get_stats(candidates)

        with patch(self.get_candidates_patch, new=lambda x: candidates):
            with patch(self.get_stats_patch, new=lambda: stats):
                with patch(
                    'aqua_voting_tracker.voting_rewards.services.rewards.base.get_market_pairs',
                    new=make_get_markets_with_soroban({1}),
                ):
                    rewards = RewardsV1Calculator().run()

        self.assertEqual(len(rewards), 2)
        classic, soroban = rewards

        # Classic: settings ratio (SDEX_SHARE=2, AMM_SHARE=5 -> amm 5/7, sdex 2/7)
        amm_ratio = Decimal(settings.AMM_SHARE) / (
            Decimal(settings.AMM_SHARE) + Decimal(settings.SDEX_SHARE)
        )
        self.assertFalse(classic.is_soroban)
        self.assertEqual(classic.amm_share, amm_ratio.quantize(Decimal('0.00')))
        self.assertEqual(classic.sdex_share, 1 - classic.amm_share)
        self.assertEqual(classic.amm_reward_value, round(classic.reward_value * amm_ratio))
        self.assertEqual(
            classic.sdex_reward_value,
            classic.reward_value - classic.amm_reward_value,
        )
        self.assertGreater(classic.sdex_reward_value, 0)

        # Soroban: everything to AMM
        self.assertTrue(soroban.is_soroban)
        self.assertEqual(soroban.amm_share, Decimal(1))
        self.assertEqual(soroban.sdex_share, Decimal(0))
        self.assertEqual(soroban.amm_reward_value, soroban.reward_value)
        self.assertEqual(soroban.sdex_reward_value, 0)

    def test_soroban_share_boost_applied_before_cap(self):
        # SOROBAN_SHARE_BOOST multiplies the voting share of soroban pairs
        # before the cap: 4% -> 6% with boost 1.5. Classic shares stay raw and
        # the dominant market still clamps to REWARD_MAX_SHARE.
        candidates = get_candidates([900, 60, 40])
        stats = get_stats(candidates)

        with override_settings(SOROBAN_SHARE_BOOST=Decimal('1.5')):
            with patch(self.get_candidates_patch, new=lambda x: candidates):
                with patch(self.get_stats_patch, new=lambda: stats):
                    with patch(
                        'aqua_voting_tracker.voting_rewards.services.rewards.base.get_market_pairs',
                        new=make_get_markets_with_soroban({2}),
                    ):
                        rewards = RewardsV1Calculator().run()

        self.assertEqual(len(rewards), 3)
        dominant, classic, soroban = rewards

        self.assertEqual(dominant.share, Decimal('0.1'))  # 0.9 clamped to the cap
        self.assertEqual(classic.share, Decimal('0.06'))  # raw, no boost
        self.assertEqual(soroban.share, Decimal('0.06'))  # 0.04 * 1.5
        self.assertEqual(
            soroban.reward_value,
            round(settings.TOTAL_REWARD_VALUE * Decimal('0.06')),
        )
        self.assertEqual(soroban.sdex_reward_value, 0)
        self.assertEqual(soroban.amm_reward_value, soroban.reward_value)
