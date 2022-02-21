from dateutil.parser import parse as date_parse

from aqua_voting_tracker.utils.stellar.asset import get_asset_string
from aqua_voting_tracker.voting.exceptions import VoteParsingError
from aqua_voting_tracker.voting.models import Vote
from aqua_voting_tracker.voting.utils import get_voting_asset


def is_locked_predicate(predicate: dict):
    return predicate == {
        'not': {
            'unconditional': True,
        },
    }


def parse_claim_after_predicate(predicate: dict):
    return predicate.get('not', {}).get('abs_before', None)


def verify_asset(claimable_balance: dict):
    asset = claimable_balance['asset']
    if asset != get_asset_string(get_voting_asset()):
        raise VoteParsingError('Invalid asset.')


def parse_claimants(claimable_balance: dict):
    sponsor = claimable_balance['sponsor']
    claimants = claimable_balance['claimants']
    if len(claimants) != 2:
        raise VoteParsingError('Invalid claimants.')

    sponsor_claimant, market_claimant = sorted(claimants, key=lambda cl: cl['destination'] == sponsor, reverse=True)

    if not is_locked_predicate(market_claimant['predicate']):
        raise VoteParsingError('Market predicate not locked.')

    balance_locked_until = parse_claim_after_predicate(sponsor_claimant['predicate'])
    if not balance_locked_until:
        raise VoteParsingError('Invalid predicate.')

    return market_claimant['destination'], sponsor_claimant['destination'], balance_locked_until


def parse_claimable_balance(claimable_balance: dict):
    verify_asset(claimable_balance)

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
        locked_at=balance_created_at,
        locked_until=locked_until,
    )
