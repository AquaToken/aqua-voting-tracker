from decimal import Decimal
from typing import List, Mapping

from django.conf import settings

from aqua_voting_tracker.voting_rewards.data import get_market_pairs, get_voting_rewards_candidate, get_voting_stats


def get_current_reward() -> List[Mapping]:
    current_stats = get_voting_stats()
    total_voting_value = Decimal(current_stats['adjusted_votes_value_sum'])

    reward_candidates = get_voting_rewards_candidate()
    reward_zone = []
    reward_zone_voting_value = 0
    for candidate in reward_candidates:
        votes_value = Decimal(candidate['adjusted_votes_value'])
        if votes_value / total_voting_value < settings.MIN_SHARE_FOR_REWARD_ZONE:
            break

        reward_zone.append({
            'market_key': candidate['market_key'],
            'votes_value': votes_value,
        })
        reward_zone_voting_value += votes_value

    market_pairs = get_market_pairs((market['market_key'] for market in reward_zone))
    market_pair_mapping = {
        market_pair['account_id']: (market_pair['asset1'], market_pair['asset2'])
        for market_pair in market_pairs
    }

    total_share = 0
    cut_share = 0
    remain_share = 1
    for reward_market in reward_zone:
        asset1, asset2 = market_pair_mapping[reward_market['market_key']]
        reward_market['asset1'] = asset1
        reward_market['asset2'] = asset2

        share = reward_market['votes_value'] / reward_zone_voting_value
        add_share = cut_share * share / remain_share
        remain_share -= share
        cut_share -= add_share
        share += add_share

        if share > settings.REWARD_MAX_SHARE:
            cut_share += share - settings.REWARD_MAX_SHARE
            share = settings.REWARD_MAX_SHARE

        reward_market['share'] = share
        total_share += share

    for reward_market in reward_zone:
        reward_market['reward_value'] = round(settings.TOTAL_REWARD_VALUE * reward_market['share'] / total_share)

        reward_market['amm_reward_value'] = round(reward_market['reward_value'] * settings.AMM_SHARE
                                                  / (settings.SDEX_SHARE + settings.AMM_SHARE))
        reward_market['sdex_reward_value'] = reward_market['reward_value'] - reward_market['amm_reward_value']
        reward_market['share'] = Decimal(round(reward_market['share'], 4))

    return reward_zone
