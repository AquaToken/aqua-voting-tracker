from typing import Iterator


class BaseMarketKeysProvider:
    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError()


def get_marketkeys_provider():
    from aqua_voting_tracker.voting.marketkeys.requests import ApiMarketKeysProvider
    return ApiMarketKeysProvider()
