import logging
from typing import Iterator, Optional, List

from stellar_sdk import Server
from stellar_sdk.call_builder.call_builder_sync import BaseCallBuilder


logger = logging.getLogger(__name__)


class StreamWorker:
    def __init__(self, horizon_url='https://horizon-testnet.stellar.org'):
        self.horizon_url = horizon_url
        self.horizon_limit = 200

    def get_server(self) -> Server:
        return Server(self.horizon_url)

    def load_cursor(self) -> Optional[str]:
        raise NotImplementedError()

    def save_cursor(self, cursor: str):
        raise NotImplementedError()

    def get_request_builder(self) -> BaseCallBuilder:
        raise NotImplementedError()

    def handle_entry(self, entry: dict):
        raise NotImplementedError()

    def load_data(self) -> Iterator[dict]:
        request = self.get_request_builder().limit(self.horizon_limit)

        cursor = self.load_cursor()
        if cursor:
            request = request.cursor(cursor)

        yield from request.stream()

    def run(self):
        for entry in self.load_data():
            logger.info('Received entry: %s', entry['id'])
            self.handle_entry(entry)


class BunchedByOperationsEffectsStreamWorker(StreamWorker):
    def __init__(self, *args, **kwargs):
        super(BunchedByOperationsEffectsStreamWorker, self).__init__(*args, **kwargs)

        self.current_operation_id: Optional[str] = None
        self.effects_bunch: List[dict] = []

    def get_request_builder(self) -> BaseCallBuilder:
        return self.get_server().effects()

    def handle_entry(self, effect: dict):
        operation_id = effect['id'].split('-')[0]
        if operation_id == self.current_operation_id:
            self.effects_bunch.append(effect)
            return

        if self.effects_bunch:
            self.handle_operation_effects(self.effects_bunch)

        self.effects_bunch = [effect]
        self.current_operation_id = operation_id

    def load_cursor(self) -> Optional[str]:
        raise NotImplementedError()

    def save_cursor(self, cursor: str):
        raise NotImplementedError()

    def handle_operation_effects(self, operation_effects: List[dict]):
        raise NotImplementedError()
