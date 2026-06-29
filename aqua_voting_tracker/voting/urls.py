from django.urls import path

from aqua_voting_tracker.voting.api import (
    MultiGetVotingSnapshotView,
    TopVolumeSnapshotView,
    TopVotedSnapshotView,
    VotingAccountStatsView,
    VotingSnapshotListView,
    VotingSnapshotStatsView,
)


urlpatterns = [
    path('market-keys/<str:market_key>/votes/', VotingAccountStatsView.as_view()),
    path('voting-snapshot/', MultiGetVotingSnapshotView.as_view()),
    path('voting-snapshot/top/', VotingSnapshotListView.as_view()),
    # Deprecated: kept as aliases of voting-snapshot/top/ with a fixed default ordering.
    path('voting-snapshot/top-volume/', TopVolumeSnapshotView.as_view()),
    path('voting-snapshot/top-voted/', TopVotedSnapshotView.as_view()),
    path('voting-snapshot/stats/', VotingSnapshotStatsView.as_view()),
]
