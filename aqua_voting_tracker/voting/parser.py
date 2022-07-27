from django.conf import settings

from dateutil.parser import parse as date_parse

from aqua_voting_tracker.voting.exceptions import VoteParsingError
from aqua_voting_tracker.voting.models import Vote


def is_locked_predicate(predicate: dict):
    return predicate == {
        'not': {
            'unconditional': True,
        },
    }


def parse_claim_after_predicate(predicate: dict):
    return predicate.get('not', {}).get('abs_before', None)


def parse_asset(claimable_balance: dict):
    asset = claimable_balance['asset']
    if asset not in settings.VOTING_ASSETS:
        raise VoteParsingError('Invalid asset.')

    return asset


def parse_claimants(claimable_balance: dict):
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


def parse_claimable_balance(claimable_balance: dict):
    asset = parse_asset(claimable_balance)

    balance_id = claimable_balance['id']
    amount = claimable_balance['amount']
    balance_created_at = claimable_balance['last_modified_time']
    market_key, voting_key, locked_until = parse_claimants(claimable_balance)

    try:
        balance_created_at = date_parse(balance_created_at)
        locked_until = date_parse(locked_until)
    except ValueError:
        raise VoteParsingError('Invalid date format.')

    return Vote(
        balance_id=balance_id,
        voting_account=voting_key,
        market_key=market_key,
        amount=amount,
        asset=asset,
        locked_at=balance_created_at,
        locked_until=locked_until,
    )
