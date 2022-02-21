from typing import Iterator, Iterable


class BaseMarketKeysProvider:
    def __iter__(self) -> Iterator[dict]:
        raise NotImplementedError()

    def get_multiple(self, account_ids: Iterable[str]) -> Iterator[dict]:
        raise NotImplementedError()
