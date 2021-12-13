from decimal import Decimal
from typing import Iterable, Mapping

from django.conf import settings

from aqua_voting_tracker.voting_rewards.data import get_market_pairs, get_voting_rewards_candidate, get_voting_stats


def get_current_reward() -> Iterable[Mapping]:
    current_stats = get_voting_stats()
    total_voting_value = Decimal(current_stats['votes_value_sum'])

    reward_candidates = get_voting_rewards_candidate()
    reward_zone = []
    reward_zone_voting_value = 0
    for candidate in reward_candidates:
        votes_value = Decimal(candidate['votes_value'])
        if votes_value / total_voting_value < settings.MIN_SHARE_FOR_REWARD_ZONE:
            break

        reward_zone.append({
            'market_key': candidate['market_key'],
            'votes_value': votes_value,
        })
        reward_zone_voting_value += votes_value

    market_pairs = get_market_pairs(map(lambda market: market['market_key'], reward_zone))
    market_pair_mapping = {
        market_pair['account_id']: (market_pair['asset1'], market_pair['asset2'])
        for market_pair in market_pairs
    }

    for reward_market in reward_zone:
        asset1, asset2 = market_pair_mapping[reward_market['market_key']]
        reward_market['asset1'] = asset1
        reward_market['asset2'] = asset2

        reward_market['share'] = Decimal(
            round(min(reward_market['votes_value'] / reward_zone_voting_value, settings.REWARD_MAX_SHARE), 2)
        )
        reward_market['reward_value'] = round(settings.TOTAL_REWARD_VALUE * reward_market['share'])

        reward_market['amm_reward_value'] = round(reward_market['reward_value'] * settings.AMM_SHARE
                                                  / (settings.SDEX_SHARE + settings.AMM_SHARE))
        reward_market['sdex_reward_value'] = reward_market['reward_value'] - reward_market['amm_reward_value']

    return reward_zone
