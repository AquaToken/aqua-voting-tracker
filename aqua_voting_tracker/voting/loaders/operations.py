from typing import Iterator

from django.conf import settings
from django.core.cache import cache

from dateutil.parser import parse as date_parse
from stellar_sdk import Server

from aqua_voting_tracker.utils.stellar.requests import load_all_records
from aqua_voting_tracker.voting.models import Vote


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

        request_builder = horizon_server.operations().order(desc=False)

        for record in load_all_records(request_builder, start_cursor=self.load_cursor(), page_size=self.PAGE_LIMIT):
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
            self.update_claimed_back_time(operation)
