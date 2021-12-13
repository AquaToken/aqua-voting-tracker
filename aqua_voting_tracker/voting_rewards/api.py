from django.core.cache import cache

from rest_framework.response import Response
from rest_framework.views import APIView

from aqua_voting_tracker.voting_rewards.constants import REWARD_CACHE_KEY


class VotingRewardsView(APIView):
    def get(self, request, *args, **kwargs):
        rewards = cache.get(REWARD_CACHE_KEY, [])
        return Response(rewards)
