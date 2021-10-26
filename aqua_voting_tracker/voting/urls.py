from django.urls import path

from aqua_voting_tracker.voting.api import MultiGetVotingSnapshotView, TopVotingSnapshotView


urlpatterns = [
    path('voting-snapshot/', MultiGetVotingSnapshotView.as_view()),
    path('voting-snapshot/top/', TopVotingSnapshotView.as_view()),
]
