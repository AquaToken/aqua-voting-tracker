from django.urls import path

from aqua_voting_tracker.voting_rewards.api import VotingRewardsView


urlpatterns = [
    path('voting-rewards/', VotingRewardsView.as_view()),
]
