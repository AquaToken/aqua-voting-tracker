import logging
from typing import List, Optional

from django.conf import settings
from django.core.cache import cache

from prometheus_client import Counter
from stellar_sdk import Asset

from aqua_voting_tracker.utils.stellar.asset import get_asset_string
from aqua_voting_tracker.utils.stellar.stream import BunchedByOperationsEffectsStreamWorker, PrometheusMetricsMixin
from aqua_voting_tracker.voting.tasks import task_parse_create_claimable_balance_effects, \
    task_parse_close_claimable_balance_effects

logger = logging.getLogger(__name__)


class EffectsStream(PrometheusMetricsMixin, BunchedByOperationsEffectsStreamWorker):
    horizon_url = settings.HORIZON_URL

    cursor_cache_key = 'aqua_voting_tracker.voting.EFFECTS_CURSOR'

    metrics_namespace = f'{settings.PROMETHEUS_METRICS_NAMESPACE}_effects_stream'

    claimable_balance_created = 'claimable_balance_created'
    claimable_balance_claimed = 'claimable_balance_claimed'
    claimable_balance_clawed_back = 'claimable_balance_clawed_back'
    account_credited = 'account_credited'

    def __init__(self, *args, **kwargs):
        super(EffectsStream, self).__init__(*args, **kwargs)

        self.processed_create_claimable_balance_counter = Counter(
            f'{self.metrics_namespace}_processed_create_claimable_balance',
            'Count of processed create claimable balance operations.',
        )
        self.processed_close_claimable_balance_counter = Counter(
            f'{self.metrics_namespace}_processed_close_claimable_balance',
            'Count of processed close claimable balance operations.',
        )

    def save_cursor(self, cursor: str):
        cache.set(self.cursor_cache_key, cursor, None)

    def load_cursor(self) -> Optional[str]:
        return cache.get(self.cursor_cache_key)

    def handle_operation_effects(self, operation_effects: List[dict]):
        effects_types = {effect['type'] for effect in operation_effects}
        if self.claimable_balance_created in effects_types:
            self.handle_create_claimable_balance(operation_effects)

        if effects_types.intersection({self.claimable_balance_claimed, self.claimable_balance_clawed_back}):
            self.handle_close_claimable_balance(operation_effects)

        self.save_cursor(operation_effects[-1]['paging_token'])

    def handle_create_claimable_balance(self, operation_effects: List[dict]):
        claimable_balance_created_effect = next(effect for effect in operation_effects
                                                if effect['type'] == self.claimable_balance_created)
        if claimable_balance_created_effect['asset'] not in settings.VOTING_ASSETS:
            return

        task_parse_create_claimable_balance_effects.delay(operation_effects)
        self.processed_create_claimable_balance_counter.inc()

    def handle_close_claimable_balance(self, operation_effects: List[dict]):
        account_credited_effect = next(effect for effect in operation_effects
                                       if effect['type'] == self.account_credited)
        if account_credited_effect['asset_type'] == 'native':
            balance_asset = get_asset_string(Asset.native())
        else:
            balance_asset = get_asset_string(Asset(
                account_credited_effect['asset_code'],
                account_credited_effect['asset_issuer'],
            ))
        if balance_asset not in settings.VOTING_ASSETS:
            return

        task_parse_close_claimable_balance_effects.delay(operation_effects)
        self.processed_close_claimable_balance_counter.inc()
