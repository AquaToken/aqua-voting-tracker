import logging
from typing import Optional, List

from django.conf import settings
from django.core.cache import cache
from prometheus_client import Counter

from aqua_voting_tracker.utils.stellar.stream import BunchedByOperationsEffectsStreamWorker, PrometheusMetricsMixin
from aqua_voting_tracker.voting.tasks import task_parse_create_claimable_balance_effects


logger = logging.getLogger(__name__)


class EffectsStream(PrometheusMetricsMixin, BunchedByOperationsEffectsStreamWorker):
    horizon_url = settings.HORIZON_URL

    cursor_cache_key = 'aqua_voting_tracker.voting.EFFECTS_CURSOR'

    metrics_namespace = f'{settings.PROMETHEUS_METRICS_NAMESPACE}_effects_stream'

    def __init__(self, *args, **kwargs):
        super(EffectsStream, self).__init__(*args, **kwargs)

        self.processed_create_claimable_balance_counter = Counter(
            f'{self.metrics_namespace}_processed_create_claimable_balance',
            'Count of processed create claimable balance operations.',
        )

    def save_cursor(self, cursor: str):
        cache.set(self.cursor_cache_key, cursor, None)

    def load_cursor(self) -> Optional[str]:
        return cache.get(self.cursor_cache_key)

    def handle_operation_effects(self, operation_effects: List[dict]):
        effects_types = set(effect['type'] for effect in operation_effects)
        if 'claimable_balance_created' in effects_types:
            self.handle_create_claimable_balance(operation_effects)

        self.save_cursor(operation_effects[-1]['paging_token'])

    def handle_create_claimable_balance(self, operation_effects: List[dict]):
        claimable_balance_created_effect = next(effect for effect in operation_effects
                                                if effect['type'] == 'claimable_balance_created')
        if claimable_balance_created_effect['asset'] in settings.VOTING_ASSETS:
            task_parse_create_claimable_balance_effects.delay(operation_effects)
            self.processed_create_claimable_balance_counter.inc()