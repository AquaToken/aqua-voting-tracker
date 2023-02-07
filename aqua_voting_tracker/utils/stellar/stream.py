import logging
from datetime import datetime, timezone
from typing import Iterator, Optional, List

from dateutil.parser import parse as date_parse
from prometheus_client import Summary, Counter
from stellar_sdk import Server
from stellar_sdk.call_builder.call_builder_sync import BaseCallBuilder


logger = logging.getLogger(__name__)


class StreamWorker:
    horizon_url = 'https://horizon-testnet.stellar.org'
    horizon_limit = 200

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


class PrometheusMetricsMixin:
    metrics_namespace = NotImplemented

    def __init__(self, *args, **kwargs):
        super(PrometheusMetricsMixin, self).__init__(*args, **kwargs)

        self.entry_delay_summary = Summary(f'{self.metrics_namespace}_receive_entry_delay',
                                           'Delay between creation of a entry and its receipt by the stream.')
        self.entry_counter = Counter(f'{self.metrics_namespace}_processed_entries',
                                     'Count of processed stream entries.')

    def get_entry_created_at(self, entry: dict) -> datetime:
        return date_parse(entry['created_at'])

    def handle_entry(self, entry: dict):
        now = datetime.now(timezone.utc)
        created_at = self.get_entry_created_at(entry)
        self.entry_delay_summary.observe((now - created_at).total_seconds())

        super(PrometheusMetricsMixin, self).handle_entry(entry)
        self.entry_counter.inc()
