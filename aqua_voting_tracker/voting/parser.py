from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Union

from django.conf import settings

from dateutil.parser import parse as date_parse

from aqua_voting_tracker.voting.exceptions import VoteParsingError
from aqua_voting_tracker.voting.models import Vote


def is_locked_predicate(predicate: dict) -> bool:
    return predicate == {
        'not': {
            'unconditional': True,
        },
    }


def parse_claim_after_predicate(predicate: dict) -> Union[datetime, timedelta, None]:
    abs_after = predicate.get('not', {}).get('abs_before', None)
    if abs_after:
        try:
            return date_parse(abs_after)
        except ValueError:
            raise VoteParsingError('Invalid date format.')

    rel_after = predicate.get('not', {}).get('rel_before', None)
    if rel_after:
        return timedelta(seconds=int(rel_after))

    return None


def parse_asset(claimable_balance: dict) -> str:
    asset = claimable_balance['asset']
    if asset not in settings.VOTING_ASSETS:
        raise VoteParsingError('Invalid asset.')

    return asset


def parse_claimants(claimable_balance: dict) -> (str, str, Union[datetime, timedelta]):
    sponsor = claimable_balance['sponsor']
    claimants = claimable_balance['claimants']
    if len(claimants) != 2:
        raise VoteParsingError('Invalid claimants.')

    claim_back_claimant, market_claimant = sorted(claimants, key=lambda cl: is_locked_predicate(cl['predicate']))
    if not is_locked_predicate(market_claimant['predicate']):
        raise VoteParsingError('Market predicate not locked.')

    if claim_back_claimant['destination'] != sponsor and sponsor != settings.VOTING_BALANCES_DISTRIBUTOR:
        raise VoteParsingError('Invalid claimant destination.')

    balance_locked_until = parse_claim_after_predicate(claim_back_claimant['predicate'])
    if not balance_locked_until:
        raise VoteParsingError('Invalid predicate.')

    return market_claimant['destination'], claim_back_claimant['destination'], balance_locked_until


def parse_claimable_balance(claimable_balance: dict) -> Vote:
    asset = parse_asset(claimable_balance)

    balance_id = claimable_balance['id']
    amount = claimable_balance['amount']
    balance_created_at = claimable_balance['last_modified_time']
    market_key, voting_key, locked_until = parse_claimants(claimable_balance)

    try:
        balance_created_at = date_parse(balance_created_at)
    except ValueError:
        raise VoteParsingError('Invalid date format.')

    if isinstance(locked_until, timedelta):
        locked_until = balance_created_at + locked_until

    return Vote(
        balance_id=balance_id,
        voting_account=voting_key,
        market_key=market_key,
        amount=amount,
        asset=asset,
        locked_at=balance_created_at,
        locked_until=locked_until,
    )


def parse_claimable_balance_created_effect(effect: dict) -> (str, str, str, Decimal, datetime):
    balance_id = effect['balance_id']
    account = effect['account']
    asset = effect['asset']
    amount = Decimal(effect['amount'])
    created_at = date_parse(effect['created_at'])

    if asset not in settings.VOTING_ASSETS:
        raise VoteParsingError('Invalid asset.')

    return balance_id, account, asset, amount, created_at


def parse_claim_back_claimant_created_effect(effect: dict) -> (str, datetime):
    account = effect['account']
    balance_locked_until = parse_claim_after_predicate(effect['predicate'])
    if not balance_locked_until:
        raise VoteParsingError('Invalid predicate.')

    if isinstance(balance_locked_until, timedelta):
        created_at = date_parse(effect['created_at'])
        balance_locked_until = created_at + balance_locked_until

    return account, balance_locked_until


def parse_market_claimant_created_effect(effect: dict) -> str:
    account = effect['account']
    if not is_locked_predicate(effect['predicate']):
        raise VoteParsingError('Invalid predicate.')

    return account


def parse_claimable_balance_from_effects(effects: List[dict]) -> Vote:
    claimable_balance_created_effect = next(
        effect for effect in effects if effect['type'] == 'claimable_balance_created'
    )

    balance_id, sponsor, asset, amount, created_at = parse_claimable_balance_created_effect(
        claimable_balance_created_effect,
    )

    if len([effect for effect in effects if effect['type'] == 'claimable_balance_claimant_created']) != 2:
        raise VoteParsingError('Invalid claimants.')
    claim_back_claimant_created_effect, market_claimant_created_effect = sorted([
        effect for effect in effects if effect['type'] == 'claimable_balance_claimant_created'
    ], key=lambda effect: is_locked_predicate(effect['predicate']))

    voting_key, locked_until = parse_claim_back_claimant_created_effect(claim_back_claimant_created_effect)
    market_key = parse_market_claimant_created_effect(market_claimant_created_effect)

    if sponsor != voting_key and sponsor != settings.VOTING_BALANCES_DISTRIBUTOR:
        raise VoteParsingError('Invalid sponsor.')

    return Vote(
        balance_id=balance_id,
        voting_account=voting_key,
        market_key=market_key,
        amount=amount,
        asset=asset,
        locked_at=created_at,
        locked_until=locked_until,
    )
