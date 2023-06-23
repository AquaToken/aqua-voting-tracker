from django.core.cache import cache

from rest_framework.response import Response
from rest_framework.views import APIView

from aqua_voting_tracker.utils.stellar.asset import parse_asset_string
from aqua_voting_tracker.voting_rewards.constants import REWARD_CACHE_KEY, REWARD_CACHE_KEY_V2


class VotingRewardsView(APIView):
    def get(self, request, *args, **kwargs):
        rewards = cache.get(REWARD_CACHE_KEY, [])
        return Response(rewards)


# TODO: Temp views. Delete after using
class VotingRewardsV2View(APIView):
    def format_reward(self, reward, last_updated):
        asset1 = parse_asset_string(reward['asset1'])
        asset2 = parse_asset_string(reward['asset2'])
        return {
            'market_key': {
                'asset1_code': asset1.code,
                'asset1_issuer': asset1.issuer,
                'asset2_code': asset2.code,
                'asset2_issuer': asset2.issuer,
            },
            'daily_sdex_reward': reward['sdex_reward_value'],
            'daily_amm_reward': reward['amm_reward_value'],
            'daily_sdex_percentage': reward['sdex_reward_percentage'],
            'daily_amm_percentage': reward['amm_reward_percentage'],
            'daily_total_reward': reward['sdex_reward_value'] + reward['amm_reward_value'],
            'last_updated': last_updated,
        }

    def get(self, request, *args, **kwargs):
        data = cache.get(REWARD_CACHE_KEY_V2, {})
        rewards = data.get('rewards', [])
        last_updated = data.get('last_updated', '1970-01-01T00:00:00Z')

        return Response({
            'count': len(rewards),
            'next': None,
            'previous': None,
            'results': [
                self.format_reward(reward, last_updated)
                for reward in rewards
            ],
        })


class VotingRewardsV2StatsView(APIView):
    def get(self, request, *args, **kwargs):
        data = cache.get(REWARD_CACHE_KEY_V2, {})
        rewards = data.get('rewards', [])

        return Response({
            'total_daily_sdex_reward': sum(reward['sdex_reward_value'] for reward in rewards),
            'total_daily_amm_reward': sum(reward['amm_reward_value'] for reward in rewards),
            'last_updated': data.get('last_updated', '1970-01-01T00:00:00Z'),
        })
