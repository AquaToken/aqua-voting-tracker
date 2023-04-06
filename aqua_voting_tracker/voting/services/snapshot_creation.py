import dataclasses
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Iterator, List

from django.conf import settings
from django.db.transaction import atomic

from aqua_voting_tracker.voting.marketkeys.base import BaseMarketKeysProvider
from aqua_voting_tracker.voting.models import Vote, VotingSnapshot, VotingSnapshotAsset


@dataclasses.dataclass
class SnapshotAssetRecord:
    asset: str

    votes_sum: str = ''
    votes_count: int = 0


@dataclasses.dataclass
class SnapshotRecord:
    market_key: str
    upvote_account_id: str
    downvote_account_id: str

    voting_boost: Decimal = 0
    voting_boost_cap: Decimal = 0

    upvote_value: Decimal = 0
    downvote_value: Decimal = 0

    voting_amount: int = 0
    votes_value: Decimal = 0

    upvote_assets: List[SnapshotAssetRecord] = dataclasses.field(default_factory=list)
    downvote_assets: List[SnapshotAssetRecord] = dataclasses.field(default_factory=list)

    adjusted_votes_value: Decimal = 0
    rank: int = None

    @property
    def boosted_value(self):
        return self.votes_value * (1 + self.voting_boost)


class SnapshotCreationUseCase:
    VOTING_MIN_TERM = settings.VOTING_MIN_TERM

    def __init__(self, market_key_provider: BaseMarketKeysProvider):
        self.market_key_provider = market_key_provider

    def get_votes_aggregation(self, timestamp: datetime) -> dict:
        # TODO
        # queryset = Vote.objects.filter_by_min_term(self.VOTING_MIN_TERM).filter_exist_at(timestamp)
        queryset = Vote.objects.filter_exist_at(timestamp)

        votes_aggregation = {}
        for stat in queryset.annotate_stats():
            market_key = stat['market_key']
            if market_key not in votes_aggregation:
                votes_aggregation[market_key] = []

            votes_aggregation[market_key].append(stat)

        return votes_aggregation

    def get_markets_data(self, market_keys: Iterable[str]) -> Iterator[SnapshotRecord]:
        yield from (
            SnapshotRecord(
                market_key=market_key['account_id'],
                upvote_account_id=market_key['upvote_account_id'],
                downvote_account_id=market_key['downvote_account_id'],
                voting_boost=Decimal(market_key.get('voting_boost', 0)),
                voting_boost_cap=Decimal(market_key.get('voting_boost_cap', 0)),
            ) for market_key in self.market_key_provider.get_multiple(market_keys)
        )

    def set_votes_value(self, snapshot: Iterable[SnapshotRecord], votes_aggregation: dict) -> Iterator[SnapshotRecord]:
        for snapshot_record in snapshot:
            upvote_stats = votes_aggregation.get(snapshot_record.upvote_account_id, [])
            downvote_stats = votes_aggregation.get(snapshot_record.downvote_account_id, [])

            if not upvote_stats and not downvote_stats:
                continue

            snapshot_record.upvote_value = 0
            snapshot_record.downvote_value = 0
            snapshot_record.votes_value = 0
            snapshot_record.voting_amount = 0
            snapshot_record.upvote_assets = []
            snapshot_record.downvote_assets = []

            for stat in upvote_stats:
                snapshot_record.upvote_value += stat['votes_value']
                snapshot_record.votes_value += stat['votes_value']
                snapshot_record.voting_amount += stat['voting_amount']
                snapshot_record.upvote_assets.append(SnapshotAssetRecord(
                    asset=stat['asset'],
                    votes_sum=str(stat['votes_value']),
                    votes_count=stat['voting_amount'],
                ))

            for stat in downvote_stats:
                snapshot_record.downvote_value += stat['votes_value']
                snapshot_record.votes_value -= stat['votes_value']
                snapshot_record.voting_amount += stat['voting_amount']
                snapshot_record.downvote_assets.append(SnapshotAssetRecord(
                    asset=stat['asset'],
                    votes_sum=str(stat['votes_value']),
                    votes_count=stat['voting_amount'],
                ))

            yield snapshot_record

    def check_voting_boost_cap(self, snapshot: Iterable[SnapshotRecord]):
        voting_boost_cap_iter = iter(snapshot_record.voting_boost_cap
                                     for snapshot_record in snapshot
                                     if snapshot_record.voting_boost_cap != 0)
        voting_boost_cap = next(voting_boost_cap_iter, 0)
        if any(cap != voting_boost_cap for cap in voting_boost_cap_iter):
            raise Exception('Error')

    def apply_boost(self, snapshot: Iterable[SnapshotRecord]) -> Iterator[SnapshotRecord]:
        snapshot = sorted(snapshot, key=lambda sr: sr.votes_value)

        self.check_voting_boost_cap(snapshot)

        fixed_total_value = 0
        controversial_markets = []
        min_limit_total_value = sum(sr.votes_value for sr in snapshot)
        for snapshot_record in snapshot:
            if snapshot_record.voting_boost == 0:
                snapshot_record.adjusted_votes_value = snapshot_record.votes_value
                fixed_total_value += snapshot_record.adjusted_votes_value
                yield snapshot_record
                continue

            boosted_total_value = min_limit_total_value - snapshot_record.votes_value + snapshot_record.boosted_value
            if snapshot_record.boosted_value / boosted_total_value < snapshot_record.voting_boost_cap:
                snapshot_record.adjusted_votes_value = snapshot_record.boosted_value
                fixed_total_value += snapshot_record.adjusted_votes_value
                min_limit_total_value = boosted_total_value
                yield snapshot_record
                continue

            controversial_markets.append(snapshot_record)

        if not controversial_markets:
            return

        boost_cap = controversial_markets[0].voting_boost_cap
        adjusted_votes_value = 0
        while True:
            if not controversial_markets:
                break

            if len(controversial_markets) >= 1 / boost_cap:
                snapshot_record = controversial_markets.pop(0)
                snapshot_record.adjusted_votes_value = snapshot_record.boosted_value
                fixed_total_value += snapshot_record.adjusted_votes_value
                yield snapshot_record
                continue

            adjusted_votes_value = fixed_total_value * boost_cap / (1 - boost_cap * len(controversial_markets))
            if adjusted_votes_value < controversial_markets[-1].votes_value:
                snapshot_record = controversial_markets.pop(-1)
                snapshot_record.adjusted_votes_value = snapshot_record.votes_value
                fixed_total_value += snapshot_record.adjusted_votes_value
                yield snapshot_record
                continue

            if adjusted_votes_value > controversial_markets[0].boosted_value:
                snapshot_record = controversial_markets.pop(0)
                snapshot_record.adjusted_votes_value = snapshot_record.boosted_value
                fixed_total_value += snapshot_record.adjusted_votes_value
                yield snapshot_record
                continue

            break

        for snapshot_record in controversial_markets:
            snapshot_record.adjusted_votes_value = adjusted_votes_value
            yield snapshot_record

    def set_rank(self, snapshot: Iterable[SnapshotRecord]):
        snapshot = sorted(snapshot, key=lambda sr: (sr.adjusted_votes_value, sr.votes_value), reverse=True)
        for index, snapshot_record in enumerate(snapshot):
            snapshot_record.rank = index + 1
            yield snapshot_record

    def save_snapshot(self, snapshot: Iterable[SnapshotRecord], timestamp: datetime):
        snapshot_objects = []
        asset_objects = []
        for snapshot_record in snapshot:
            voting_snapshot = VotingSnapshot(
                market_key=snapshot_record.market_key,
                rank=snapshot_record.rank,

                votes_value=snapshot_record.votes_value,
                voting_amount=snapshot_record.voting_amount,

                upvote_value=snapshot_record.upvote_value,
                downvote_value=snapshot_record.downvote_value,

                adjusted_votes_value=snapshot_record.adjusted_votes_value,

                timestamp=timestamp,

                extra={
                    'upvote_assets': [dataclasses.asdict(record) for record in snapshot_record.upvote_assets],
                    'downvote_assets': [dataclasses.asdict(record) for record in snapshot_record.downvote_assets],
                },
            )
            snapshot_objects.append(voting_snapshot)

            for asset_record in snapshot_record.upvote_assets:
                asset_objects.append(VotingSnapshotAsset(
                    snapshot=voting_snapshot,
                    asset=asset_record.asset,
                    direction=VotingSnapshotAsset.Direction.UP,
                    votes_sum=asset_record.votes_sum,
                    votes_count=asset_record.votes_count,
                ))
            for asset_record in snapshot_record.downvote_assets:
                asset_objects.append(VotingSnapshotAsset(
                    snapshot=voting_snapshot,
                    asset=asset_record.asset,
                    direction=VotingSnapshotAsset.Direction.DOWN,
                    votes_sum=asset_record.votes_sum,
                    votes_count=asset_record.votes_count,
                ))

        with atomic():
            VotingSnapshot.objects.bulk_create(snapshot_objects)
            VotingSnapshotAsset.objects.bulk_create(asset_objects)

    def create_snapshot(self, timestamp: datetime):
        votes_aggregation = self.get_votes_aggregation(timestamp)

        snapshot = self.get_markets_data(votes_aggregation.keys())

        snapshot = self.set_votes_value(snapshot, votes_aggregation)

        snapshot = self.apply_boost(snapshot)

        snapshot = self.set_rank(snapshot)

        self.save_snapshot(snapshot, timestamp)
