from decimal import Decimal
from typing import Iterable
from unittest import TestCase

from aqua_voting_tracker.voting.marketkeys.base import BaseMarketKeysProvider
from aqua_voting_tracker.voting.services.snapshot_creation import SnapshotCreationUseCase, SnapshotRecord


class BoostApplyTest(TestCase):
    def setUp(self):
        self.use_case = SnapshotCreationUseCase(BaseMarketKeysProvider())

    @staticmethod
    def create_snapshot_record(market_key: str, votes_value: Decimal, boosted=True):
        if boosted:
            voting_boost = Decimal('0.5')
            voting_boost_cap = Decimal('0.05')
        else:
            voting_boost = Decimal(0)
            voting_boost_cap = Decimal(0)

        return SnapshotRecord(
            market_key=market_key,
            upvote_account_id='',
            downvote_account_id='',
            votes_value=votes_value,
            voting_boost=voting_boost,
            voting_boost_cap=voting_boost_cap,
        )

    @staticmethod
    def create_snapshot_pattern(market_key: str, adjusted_votes_value: Decimal):
        return SnapshotRecord(
            market_key=market_key,
            upvote_account_id='',
            downvote_account_id='',
            adjusted_votes_value=adjusted_votes_value,
        )

    def assert_snapshot(self, first: Iterable[SnapshotRecord], second: Iterable[SnapshotRecord]):
        first = sorted(first, key=lambda sr: (sr.adjusted_votes_value, sr.market_key))
        second = sorted(second, key=lambda sr: (sr.adjusted_votes_value, sr.market_key))

        self.assertEqual(len(first), len(second))
        for first_record, second_record in zip(first, second):
            msg = f'Different elements: ({first_record.market_key}, {first_record.adjusted_votes_value}) != ' \
                  f'({second_record.market_key}, {second_record.adjusted_votes_value})'
            self.assertEqual(first_record.market_key, second_record.market_key, msg)
            self.assertAlmostEqual(float(first_record.adjusted_votes_value), float(second_record.adjusted_votes_value),
                                   places=7, msg=msg)

    def check_snapshot(self, snapshot: Iterable[SnapshotRecord]):
        snapshot = list(snapshot)
        total = sum(sr.adjusted_votes_value for sr in snapshot)

        for snapshot_record in snapshot:
            msg = f'Invalid record: {snapshot_record}'
            if snapshot_record.voting_boost == 0:
                self.assertEqual(snapshot_record.adjusted_votes_value, snapshot_record.votes_value, msg=msg)
                continue

            if snapshot_record.adjusted_votes_value / total > snapshot_record.voting_boost_cap:
                self.assertEqual(snapshot_record.adjusted_votes_value, snapshot_record.votes_value, msg=msg)
                continue

            if snapshot_record.adjusted_votes_value == snapshot_record.boosted_value:
                self.assertTrue(snapshot_record.adjusted_votes_value / total <= snapshot_record.voting_boost_cap,
                                msg=msg)
                continue

            self.assertAlmostEqual(float(snapshot_record.adjusted_votes_value / total),
                                   float(snapshot_record.voting_boost_cap),
                                   places=7, msg=msg)

    def test1(self):
        snapshot = [
            self.create_snapshot_record('key1', Decimal(10000)),
            self.create_snapshot_record('key2', Decimal(500)),
            self.create_snapshot_record('key3', Decimal(400)),
            self.create_snapshot_record('key4', Decimal(100)),
            self.create_snapshot_record('key5', Decimal(50)),
        ]

        snapshot = list(self.use_case.apply_boost(snapshot))

        self.check_snapshot(snapshot)

        self.assert_snapshot(snapshot, [
            self.create_snapshot_pattern('key1', Decimal(10000)),
            self.create_snapshot_pattern('key2', Decimal('568.0555556')),
            self.create_snapshot_pattern('key3', Decimal('568.0555556')),
            self.create_snapshot_pattern('key4', Decimal(150)),
            self.create_snapshot_pattern('key5', Decimal(75)),
        ])

    def test2(self):
        snapshot = [
            self.create_snapshot_record(f'key{i}', Decimal(10)) for i in range(18)
        ] + [
            self.create_snapshot_record('key18', Decimal(8)),
            self.create_snapshot_record('key19', Decimal(12)),
        ]

        snapshot = list(self.use_case.apply_boost(snapshot))

        self.check_snapshot(snapshot)

        self.assert_snapshot(snapshot, [
            self.create_snapshot_pattern(f'key{i}', Decimal(12)) for i in range(20)
        ])

    def test3(self):
        snapshot = [
            self.create_snapshot_record('key1', Decimal(10000)),
            self.create_snapshot_record('key2', Decimal(500)),
            self.create_snapshot_record('key3', Decimal(378)),
            self.create_snapshot_record('key4', Decimal(100)),
            self.create_snapshot_record('key5', Decimal(50)),
        ]

        snapshot = list(self.use_case.apply_boost(snapshot))

        self.check_snapshot(snapshot)

        self.assert_snapshot(snapshot, [
            self.create_snapshot_pattern('key1', Decimal(10000)),
            self.create_snapshot_pattern('key2', Decimal(568)),
            self.create_snapshot_pattern('key3', Decimal(567)),
            self.create_snapshot_pattern('key4', Decimal(150)),
            self.create_snapshot_pattern('key5', Decimal(75)),
        ])

    def test4(self):
        snapshot = [
            self.create_snapshot_record('key1', Decimal(10000)),
            self.create_snapshot_record('key2', Decimal(10000), boosted=False),
            self.create_snapshot_record('key3', Decimal(450), boosted=False),
            self.create_snapshot_record('key4', Decimal(500)),
            self.create_snapshot_record('key5', Decimal(400)),
            self.create_snapshot_record('key6', Decimal(100)),
            self.create_snapshot_record('key7', Decimal(50)),
            self.create_snapshot_record('key8', Decimal(1000)),
        ]

        snapshot = list(self.use_case.apply_boost(snapshot))

        self.check_snapshot(snapshot)

        self.assert_snapshot(snapshot, [
            self.create_snapshot_pattern('key1', Decimal(10000)),
            self.create_snapshot_pattern('key2', Decimal(10000)),
            self.create_snapshot_pattern('key3', Decimal(450)),
            self.create_snapshot_pattern('key4', Decimal(750)),
            self.create_snapshot_pattern('key5', Decimal(600)),
            self.create_snapshot_pattern('key6', Decimal(150)),
            self.create_snapshot_pattern('key7', Decimal(75)),
            self.create_snapshot_pattern('key8', Decimal('1159.2105263')),
        ])

    def test5(self):
        snapshot = [
            self.create_snapshot_record('key1', Decimal(10000), boosted=False),
            self.create_snapshot_record('key2', Decimal(450), boosted=False),
            self.create_snapshot_record('key3', Decimal(150), boosted=False),
        ]

        snapshot = list(self.use_case.apply_boost(snapshot))

        self.check_snapshot(snapshot)

        self.assert_snapshot(snapshot, [
            self.create_snapshot_pattern('key1', Decimal(10000)),
            self.create_snapshot_pattern('key2', Decimal(450)),
            self.create_snapshot_pattern('key3', Decimal(150)),
        ])
