from django.urls import path

from aqua_voting_tracker.voting_rewards.api import VotingRewardsV2StatsView, VotingRewardsV2View, VotingRewardsView


urlpatterns = [
    path('voting-rewards/', VotingRewardsView.as_view()),
    path('voting-rewards-v2/', VotingRewardsV2View.as_view()),
    path('voting-rewards-v2-stats/', VotingRewardsV2StatsView.as_view()),
]
