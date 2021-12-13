from django.core.cache import cache

from aqua_voting_tracker.taskapp import app as celery_app
from aqua_voting_tracker.voting_rewards.constants import REWARD_CACHE_KEY
from aqua_voting_tracker.voting_rewards.rewards import get_current_reward


@celery_app.task(ignore_result=True)
def task_update_rewards():
    rewards = get_current_reward()
    cleaned_rewards = [
        {
            'asset1': reward['asset1'],
            'asset2': reward['asset2'],
            'sdex_reward_value': reward['sdex_reward_value'],
            'amm_reward_value': reward['amm_reward_value'],
        }
        for reward in rewards
    ]
    cache.set(REWARD_CACHE_KEY, cleaned_rewards, None)
