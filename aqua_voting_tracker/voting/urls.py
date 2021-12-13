from django.urls import path

from aqua_voting_tracker.voting.api import MultiGetVotingSnapshotView, TopVolumeSnapshotView, VotingSnapshotStatsView


urlpatterns = [
    path('voting-snapshot/', MultiGetVotingSnapshotView.as_view()),
    path('voting-snapshot/top-volume/', TopVolumeSnapshotView.as_view()),
    path('voting-snapshot/stats/', VotingSnapshotStatsView.as_view()),
]
