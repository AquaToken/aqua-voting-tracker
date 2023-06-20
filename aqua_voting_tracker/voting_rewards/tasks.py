from django.core.cache import cache
from django.utils import timezone

from aqua_voting_tracker.taskapp import app as celery_app
from aqua_voting_tracker.voting_rewards.constants import REWARD_CACHE_KEY, REWARD_CACHE_KEY_V2
from aqua_voting_tracker.voting_rewards.services.rewards.v1 import RewardsV1Calculator
from aqua_voting_tracker.voting_rewards.services.rewards.v2 import RewardsV2Calculator


@celery_app.task(ignore_result=True)
def task_update_rewards():
    rewards = RewardsV1Calculator().run()
    cleaned_rewards = [
        {
            'asset1': reward.asset1,
            'asset2': reward.asset2,
            'sdex_reward_value': reward.sdex_reward_value,
            'amm_reward_value': reward.amm_reward_value,
        }
        for reward in rewards
    ]
    cache.set(REWARD_CACHE_KEY, cleaned_rewards, None)


@celery_app.task(ignore_result=True)
def task_update_rewards_v2():
    rewards = RewardsV2Calculator().run()
    cleaned_rewards = [
        {
            'asset1': reward.asset1,
            'asset2': reward.asset2,
            'sdex_reward_value': reward.sdex_reward_value,
            'amm_reward_value': reward.amm_reward_value,
        }
        for reward in rewards
    ]
    cache.set(REWARD_CACHE_KEY_V2, {
        'last_updated': timezone.now().isoformat().replace('+00:00', 'Z'),
        'rewards': cleaned_rewards,
    }, None)
