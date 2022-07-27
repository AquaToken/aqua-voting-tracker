import asyncio
import logging
import sys
from asyncio import Semaphore
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
from aqua_voting_tracker.voting.models import Vote
from aqua_voting_tracker.voting.parser import parse_claimable_balance
from aqua_voting_tracker.voting.services.snapshot_creation import SnapshotCreationUseCase
from aqua_voting_tracker.voting.utils import get_voting_asset


logger = logging.getLogger()


CLAIMABLE_BALANCES_CURSOR_CACHE_KEY = 'aqua_voting_tracker.voting.CLAIMABLE_BALANCES_CURSOR_CACHE_KEY'
CLAIMABLE_BALANCES_LIMIT = 200
CLAIMABLE_BALANCES_BULK_LIMIT = 10000

CLAIM_BACK_CURSOR_CACHE_KEY = 'aqua_voting_tracker.voting.CLAIM_BACK_CURSOR_CACHE_KEY'
CLAIM_BACK_BUNCH_LIMIT = 250
CLAIM_BACK_REQUEST_TIMEOUT = 60
CLAIM_BACK_SEMAPHORE = 30


def _parse_vote(claimable_balance: dict):
    try:
        return parse_claimable_balance(claimable_balance)
    except VoteParsingError:
        logger.warning('Invalid claimable balance.', exc_info=sys.exc_info())


@celery_app.task(ignore_result=True)
def task_load_new_claimable_balances():
    horizon_server = Server(settings.HORIZON_URL)

    request_builder = horizon_server.claimable_balances().order(desc=False)

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

    if operation['type'] in ['claim_claimable_balance', 'clawback_claimable_balance']:
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

    SnapshotCreationUseCase(
        get_marketkeys_provider(),
    ).create_snapshot(timestamp)
