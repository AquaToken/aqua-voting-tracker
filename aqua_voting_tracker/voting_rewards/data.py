from typing import Iterable, Mapping

import requests
from django.conf import settings

from aqua_voting_tracker.voting.models import VotingSnapshot
from aqua_voting_tracker.voting.serializers import VotingSnapshotSerializer, VotingSnapshotStatsSerializer


def get_voting_rewards_candidate() -> Iterable[Mapping]:
    queryset = VotingSnapshot.objects.filter_last_snapshot().order_by('-votes_value')[:100]
    return VotingSnapshotSerializer(instance=queryset, many=True).data


def get_voting_stats() -> Mapping:
    stats = VotingSnapshot.objects.current_stats()
    return VotingSnapshotStatsSerializer(instance=stats).data


def get_market_pairs(market_keys: Iterable[str]) -> Iterable[Mapping]:
    market_keys_tracker_url = settings.MARKETKEYS_TRACKER_URL.rstrip('/')
    resp = requests.get(f'{market_keys_tracker_url}/api/market-keys/',
                        params=[('account_id', market_key) for market_key in market_keys])
    return resp.json()['results']