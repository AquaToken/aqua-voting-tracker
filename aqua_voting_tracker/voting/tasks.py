import asyncio
import decimal
import logging
import sys
from asyncio import Semaphore
from decimal import Decimal
from typing import Iterable

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from asgiref.sync import sync_to_async
from dateutil.parser import parse as date_parse
from stellar_sdk import AiohttpClient, Server, ServerAsync

from aqua_voting_tracker.taskapp import app as celery_app
from aqua_voting_tracker.utils.stellar.requests import load_all_records
from aqua_voting_tracker.voting.exceptions import VoteParsingError
from aqua_voting_tracker.voting.marketkeys import get_marketkeys_provider
from aqua_voting_tracker.voting.models import Vote, VotingSnapshot
from aqua_voting_tracker.voting.parser import parse_claimable_balance
from aqua_voting_tracker.voting.utils import get_voting_asset


logger = logging.getLogger()


CLAIMABLE_BALANCES_CURSOR_CACHE_KEY = 'aqua_voting_tracker.voting.CLAIMABLE_BALANCES_CURSOR_CACHE_KEY'
CLAIMABLE_BALANCES_LIMIT = 200
CLAIMABLE_BALANCES_BULK_LIMIT = 10000

CLAIM_BACK_CURSOR_CACHE_KEY = 'aqua_voting_tracker.voting.CLAIM_BACK_CURSOR_CACHE_KEY'
CLAIM_BACK_BUNCH_LIMIT = 300
CLAIM_BACK_REQUEST_TIMEOUT = 60
CLAIM_BACK_SEMAPHORE = 15


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
                  None)

    Vote.objects.bulk_create(new_votes)


async def _update_claim_back_time(vote: Vote, *, server: ServerAsync, semaphore: Semaphore):
    async with semaphore:
        response = await server.operations().for_claimable_balance(vote.balance_id).order(desc=True).limit(1).call()
    operation = response['_embedded']['records'][0]

    if operation['type'] != 'claim_claimable_balance':
        return

    vote.claimed_back_at = date_parse(operation['created_at'])
    await sync_to_async(vote.save)()


async def _bunch_update_claim_back_time(votes: Iterable[Vote]):
    semaphore = Semaphore(CLAIM_BACK_SEMAPHORE)
    client = AiohttpClient(request_timeout=CLAIM_BACK_REQUEST_TIMEOUT)
    async with ServerAsync(settings.HORIZON_URL, client=client) as server:
        await asyncio.gather(*[_update_claim_back_time(vote, server=server, semaphore=semaphore)
                               for vote in votes])


@celery_app.task(ignore_result=True)
def task_update_claim_back_time():
    now = timezone.now()
    queryset = Vote.objects.filter(locked_until__lt=now, claimed_back_at__isnull=True)
    cursor = cache.get(CLAIM_BACK_CURSOR_CACHE_KEY)
    if cursor:
        queryset = queryset.filter(id__gt=cursor)

    votes = list(queryset[:CLAIM_BACK_BUNCH_LIMIT])
    asyncio.run(_bunch_update_claim_back_time(votes))

    if len(votes) < CLAIM_BACK_BUNCH_LIMIT:
        cache.delete(CLAIM_BACK_CURSOR_CACHE_KEY)
    else:
        cache.set(CLAIM_BACK_CURSOR_CACHE_KEY, votes[-1].id, None)


@celery_app.task(ignore_result=True)
def task_create_voting_snapshot():
    now = timezone.now()
    timestamp = now.replace(minute=now.minute // 5 * 5, second=0, microsecond=0) - timezone.timedelta(minutes=5)

    queryset = Vote.objects.filter_by_min_term(settings.VOTING_MIN_TERM).filter_exist_at(timestamp)
    votes_aggregation = {
        stat['market_key']: stat
        for stat in queryset.annotate_stats()
    }

    market_key_provider = get_marketkeys_provider()
    snapshot_list = []
    adjusted_votes_total = 0
    voting_boost_cap_dict = {}
    for market_key in market_key_provider.get_multiple(votes_aggregation.keys()):
        upvote_stats = votes_aggregation.get(market_key['upvote_account_id'])
        downvote_stats = votes_aggregation.get(market_key['downvote_account_id'])

        if not upvote_stats and not downvote_stats:
            continue

        snapshot = VotingSnapshot(
            market_key=market_key['account_id'],
            timestamp=timestamp,
            votes_value=0,
            voting_amount=0,
        )

        if upvote_stats:
            snapshot.upvote_value = upvote_stats['votes_value']
            snapshot.votes_value += upvote_stats['votes_value']
            snapshot.voting_amount += upvote_stats['voting_amount']
        else:
            snapshot.upvote_value = 0

        if downvote_stats:
            snapshot.downvote_value = downvote_stats['votes_value']
            snapshot.votes_value -= downvote_stats['votes_value']
            snapshot.voting_amount += downvote_stats['voting_amount']
        else:
            snapshot.downvote_value = 0

        try:
            voting_boost = Decimal(market_key.get('voting_boost', 0))
            voting_boost_cap = Decimal(market_key.get('voting_boost_cap', 0))
        except decimal.InvalidOperation:
            voting_boost = 0
            voting_boost_cap = 0

        if voting_boost_cap:
            voting_boost_cap_dict[market_key['account_id']] = voting_boost_cap

        snapshot.adjusted_votes_value = snapshot.votes_value * (1 + voting_boost)
        adjusted_votes_total += snapshot.adjusted_votes_value

        snapshot_list.append(snapshot)

    snapshot_list = sorted(snapshot_list, key=lambda s: s.adjusted_votes_value, reverse=True)
    for snapshot in snapshot_list:
        voting_boost_cap = voting_boost_cap_dict.get(snapshot.market_key, 0)
        if snapshot.adjusted_votes_value / adjusted_votes_total > voting_boost_cap:
            adjusted_votes_total_except_current = adjusted_votes_total - snapshot.adjusted_votes_value

            # Solution of equality:
            # adjusted_votes_value / (adjusted_votes_value + adjusted_votes_total_except_current) = voting_boost_cap
            adjusted_votes_value = adjusted_votes_total_except_current * voting_boost_cap / (1 - voting_boost_cap)
            snapshot.adjusted_votes_value = max(adjusted_votes_value, snapshot.votes_value)

            adjusted_votes_total = adjusted_votes_total_except_current + snapshot.adjusted_votes_value

    snapshot_list = sorted(snapshot_list, key=lambda s: s.adjusted_votes_value, reverse=True)
    for index, snapshot in enumerate(snapshot_list):
        snapshot.rank = index + 1

    VotingSnapshot.objects.bulk_create(snapshot_list)
