from typing import Iterator

from django.conf import settings

import requests

from aqua_voting_tracker.voting.marketkeys.base import BaseMarketKeysProvider


class ApiMarketKeysProvider(BaseMarketKeysProvider):
    market_keys_tracker_host = settings.MARKETKEYS_TRACKER_URL
    api_endpoint = '/api/market-keys/'

    def get_api_endpoint(self):
        return self.market_keys_tracker_host.rstrip('/') + self.api_endpoint

    def __iter__(self) -> Iterator[str]:
        page_endpoint = self.get_api_endpoint() + '?limit=200'

        while page_endpoint:
            response = requests.get(page_endpoint)
            response.raise_for_status()

            data = response.json()
            records = data['results']
            page_endpoint = data['next']

            for record in records:
                yield record['account_id']
