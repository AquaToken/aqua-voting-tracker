import logging
import sys

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from stellar_sdk import Server

from aqua_voting_tracker.taskapp import app as celery_app
from aqua_voting_tracker.utils.stellar.requests import load_all_records
from aqua_voting_tracker.voting.exceptions import VoteParsingError
from aqua_voting_tracker.voting.marketkeys.base import get_marketkeys_provider
from aqua_voting_tracker.voting.models import Vote, VotingSnapshot
from aqua_voting_tracker.voting.parser import parse_claimable_balance
from aqua_voting_tracker.voting.utils import get_voting_asset


logger = logging.getLogger()


CLAIMABLE_BALANCES_CURSOR_CACHE_KEY = 'aqua_voting_tracker.voting.CLAIMABLE_BALANCES_CURSOR_CACHE_KEY'
CLAIMABLE_BALANCES_CACHE_TIMEOUT = None  # Forever
CLAIMABLE_BALANCES_LIMIT = 200
CLAIMABLE_BALANCES_BULK_LIMIT = 10000


def _parse_vote(claimable_balance: dict):
    try:
        return parse_claimable_balance(claimable_balance)
    except VoteParsingError:
        logger.warning('Invalid claimable balance.', exc_info=sys.exc_info())


@celery_app.task(ignore_result=True)
def task_load_new_claimable_balances():
    horizon_server = Server(settings.HORIZON_URL)

    request_builder = horizon_server.claimable_balances().for_asset(get_voting_asset()).order(desc=False)

    cursor = cache.get(CLAIMABLE_BALANCES_CURSOR_CACHE_KEY, None)

    last_claimable_balance = None
    new_votes = []
    for index, claimable_balance in enumerate(load_all_records(request_builder,
                                                               start_cursor=cursor,
                                                               page_size=CLAIMABLE_BALANCES_LIMIT)):
        if index > CLAIMABLE_BALANCES_BULK_LIMIT:
            break

        vote = _parse_vote(claimable_balance)
        if vote:
            new_votes.append(vote)

        last_claimable_balance = claimable_balance

    if last_claimable_balance:
        cache.set(CLAIMABLE_BALANCES_CURSOR_CACHE_KEY,
                  last_claimable_balance['paging_token'],
                  CLAIMABLE_BALANCES_CACHE_TIMEOUT)

    Vote.objects.bulk_create(new_votes)


@celery_app.task(ignore_result=True)
def task_create_voting_snapshot():
    now = timezone.now()
    timestamp = now.replace(hour=0, minute=0, second=0, microsecond=0)

    marketkeys_provider = get_marketkeys_provider()
    vote_queryset = Vote.objects.filter(market_key__in=iter(marketkeys_provider))
    VotingSnapshot.objects.create_for_timestamp(timestamp, vote_queryset=vote_queryset)
