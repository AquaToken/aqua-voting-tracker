import logging
from typing import Iterator

from django.conf import settings
from django.core.cache import cache

from dateutil.parser import parse as date_parse
from stellar_sdk import Server

from aqua_voting_tracker.voting.models import Vote


logger = logging.getLogger(__name__)


class OperationLoader:
    HORIZON_URL = settings.HORIZON_URL

    CURSOR_CACHE_KEY = 'aqua_voting_tracker.voting.OPERATIONS_CURSOR_CACHE_KEY'
    PAGE_LIMIT = 200

    def get_server(self) -> Server:
        return Server(self.HORIZON_URL)

    def load_cursor(self):
        return cache.get(self.CURSOR_CACHE_KEY)

    def save_cursor(self, cursor):
        cache.set(self.CURSOR_CACHE_KEY, cursor, None)

    def load_operations(self) -> Iterator[dict]:
        horizon_server = self.get_server()

        cursor = self.load_cursor()
        request_builder = horizon_server.operations().order(desc=False).limit(self.PAGE_LIMIT)
        if cursor:
            request_builder = request_builder.cursor(cursor)

        for record in request_builder.stream():
            yield record

            self.save_cursor(record['paging_token'])

    def update_claimed_back_time(self, operation):
        if operation['type'] != 'claim_claimable_balance':
            return

        balance_id = operation['balance_id']
        claimed_back_at = date_parse(operation['created_at'])
        Vote.objects.filter(balance_id=balance_id).update(claimed_back_at=claimed_back_at)

    def run(self):
        for operation in self.load_operations():
            logger.info(f'Process operation id: {operation["id"]}')

            self.update_claimed_back_time(operation)
