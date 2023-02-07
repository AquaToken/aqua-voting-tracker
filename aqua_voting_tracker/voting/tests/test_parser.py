from datetime import datetime, timezone
from decimal import Decimal
from unittest import TestCase

from aqua_voting_tracker.voting.parser import parse_claimable_balance, parse_claimable_balance_from_effects


class ParseClaimableBalanceTests(TestCase):
    def test_common_case(self):
        claimable_balance = {
            'id': '00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'asset': 'TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO',
            'amount': '5.0000000',
            'sponsor': 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF',
            'last_modified_ledger': 38600000,
            'last_modified_time': '2021-12-06T18:15:25Z',
            'claimants': [
                {
                    'destination': 'GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74',
                    'predicate': {
                        'not': {
                            'unconditional': True,
                        },
                    },
                },
                {
                    'destination': 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF',
                    'predicate': {
                        'not': {
                            'abs_before': '2022-06-06T18:15:25Z',
                            'abs_before_epoch': '1654528525',
                        },
                    },
                },
            ],
            'flags': {
                'clawback_enabled': False,
            },
            'paging_token': '38600000-00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        }

        vote = parse_claimable_balance(claimable_balance)

        self.assertEqual(vote.balance_id, '00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.assertEqual(vote.voting_account, 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF')
        self.assertEqual(vote.market_key, 'GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74')
        self.assertEqual(Decimal(vote.amount), Decimal(5))
        self.assertEqual(vote.asset, 'TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO')
        self.assertEqual(vote.locked_at, datetime(2021, 12, 6, 18, 15, 25, tzinfo=timezone.utc))
        self.assertEqual(vote.locked_until, datetime(2022, 6, 6, 18, 15, 25, tzinfo=timezone.utc))

    def test_balance_from_distributor(self):
        claimable_balance = {
            'id': '00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'asset': 'TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO',
            'amount': '5.0000000',
            'sponsor': 'GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO',
            'last_modified_ledger': 38600000,
            'last_modified_time': '2021-12-06T18:15:25Z',
            'claimants': [
                {
                    'destination': 'GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74',
                    'predicate': {
                        'not': {
                            'unconditional': True,
                        },
                    },
                },
                {
                    'destination': 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF',
                    'predicate': {
                        'not': {
                            'abs_before': '2022-06-06T18:15:25Z',
                            'abs_before_epoch': '1654528525',
                        },
                    },
                },
            ],
            'flags': {
                'clawback_enabled': False,
            },
            'paging_token': '38600000-00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        }

        vote = parse_claimable_balance(claimable_balance)

        self.assertEqual(vote.balance_id, '00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.assertEqual(vote.voting_account, 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF')
        self.assertEqual(vote.market_key, 'GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74')
        self.assertEqual(Decimal(vote.amount), Decimal(5))
        self.assertEqual(vote.asset, 'TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO')
        self.assertEqual(vote.locked_at, datetime(2021, 12, 6, 18, 15, 25, tzinfo=timezone.utc))
        self.assertEqual(vote.locked_until, datetime(2022, 6, 6, 18, 15, 25, tzinfo=timezone.utc))


class ParseClaimableBalanceEffectTests(TestCase):
    def test_common_case(self):
        effects = [
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000001",
                "paging_token": "xxxxxxxxxxxxxxxxxx-1",
                "account": "GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF",
                "type": "claimable_balance_created",
                "type_i": 50,
                "created_at": "2021-12-06T18:15:25Z",
                "asset": "TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "amount": "5.0000000"
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000002",
                "paging_token": "xxxxxxxxxxxxxxxxxx-2",
                "account": "GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74",
                "type": "claimable_balance_claimant_created",
                "type_i": 51,
                "created_at": "2021-12-06T18:15:25Z",
                "asset": "TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "amount": "5.0000000",
                "predicate": {
                    "not": {
                        "unconditional": True
                    }
                }
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000003",
                "paging_token": "xxxxxxxxxxxxxxxxxx-3",
                "account": "GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF",
                "type": "claimable_balance_claimant_created",
                "type_i": 51,
                "created_at": "2021-12-06T18:15:25Z",
                "asset": "TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "amount": "5.0000000",
                "predicate": {
                    "not": {
                        'abs_before': '2022-06-06T18:15:25Z',
                        'abs_before_epoch': '1654528525',
                    }
                }
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000004",
                "paging_token": "xxxxxxxxxxxxxxxxxx-4",
                "account": "GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF",
                "type": "account_debited",
                "type_i": 3,
                "created_at": "2021-12-06T18:15:25Z",
                "asset_type": "credit_alphanum4",
                "asset_code": "TEST",
                "asset_issuer": "GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "amount": "5.0000000"
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000005",
                "paging_token": "xxxxxxxxxxxxxxxxxx-5",
                "account": "GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF",
                "type": "claimable_balance_sponsorship_created",
                "type_i": 69,
                "created_at": "2021-12-06T18:15:25Z",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "sponsor": "GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF"
            }
        ]

        vote = parse_claimable_balance_from_effects(effects)

        self.assertEqual(vote.balance_id, '00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.assertEqual(vote.voting_account, 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF')
        self.assertEqual(vote.market_key, 'GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74')
        self.assertEqual(Decimal(vote.amount), Decimal(5))
        self.assertEqual(vote.asset, 'TEST:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO')
        self.assertEqual(vote.locked_at, datetime(2021, 12, 6, 18, 15, 25, tzinfo=timezone.utc))
        self.assertEqual(vote.locked_until, datetime(2022, 6, 6, 18, 15, 25, tzinfo=timezone.utc))

    def test_balance_from_distributor(self):
        effects = [
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000001",
                "paging_token": "xxxxxxxxxxxxxxxxxx-1",
                "account": "GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "type": "claimable_balance_created",
                "type_i": 50,
                "created_at": "2021-12-06T18:15:25Z",
                "asset": "TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "amount": "5.0000000"
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000002",
                "paging_token": "xxxxxxxxxxxxxxxxxx-2",
                "account": "GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74",
                "type": "claimable_balance_claimant_created",
                "type_i": 51,
                "created_at": "2021-12-06T18:15:25Z",
                "asset": "TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "amount": "5.0000000",
                "predicate": {
                    "not": {
                        "unconditional": True
                    }
                }
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000003",
                "paging_token": "xxxxxxxxxxxxxxxxxx-3",
                "account": "GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF",
                "type": "claimable_balance_claimant_created",
                "type_i": 51,
                "created_at": "2021-12-06T18:15:25Z",
                "asset": "TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "amount": "5.0000000",
                "predicate": {
                    "not": {
                        'abs_before': '2022-06-06T18:15:25Z',
                        'abs_before_epoch': '1654528525',
                    }
                }
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000004",
                "paging_token": "xxxxxxxxxxxxxxxxxx-4",
                "account": "GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "type": "account_debited",
                "type_i": 3,
                "created_at": "2021-12-06T18:15:25Z",
                "asset_type": "credit_alphanum4",
                "asset_code": "TEST2",
                "asset_issuer": "GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "amount": "5.0000000"
            },
            {
                "id": "xxxxxxxxxxxxxxxxxxx-0000000005",
                "paging_token": "xxxxxxxxxxxxxxxxxx-5",
                "account": "GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO",
                "type": "claimable_balance_sponsorship_created",
                "type_i": 69,
                "created_at": "2021-12-06T18:15:25Z",
                "balance_id": "00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "sponsor": "GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO"
            }
        ]

        vote = parse_claimable_balance_from_effects(effects)

        self.assertEqual(vote.balance_id, '00000000xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.assertEqual(vote.voting_account, 'GBB6R36ZT74EJO6OZ2NYDXTQ5VRU777QPNOSO76IWDQBV2CBUBTOLKOF')
        self.assertEqual(vote.market_key, 'GBCH3CNHAZA7EPPWNKJJXWUDEGSDWRP4UYRYK6HEHBK6A7OHCUWO6B74')
        self.assertEqual(Decimal(vote.amount), Decimal(5))
        self.assertEqual(vote.asset, 'TEST2:GBY6X4AJJEXS536TRURTET5AXETIQFICOM6LTTIIUF7G77F6FSVGZAIO')
        self.assertEqual(vote.locked_at, datetime(2021, 12, 6, 18, 15, 25, tzinfo=timezone.utc))
        self.assertEqual(vote.locked_until, datetime(2022, 6, 6, 18, 15, 25, tzinfo=timezone.utc))
