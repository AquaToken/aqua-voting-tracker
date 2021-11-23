from django.urls import path

from aqua_voting_tracker.voting.api import MultiGetVotingSnapshotView, TopVotedSnapshotView, TopVolumeSnapshotView


urlpatterns = [
    path('voting-snapshot/', MultiGetVotingSnapshotView.as_view()),
    path('voting-snapshot/top-voted/', TopVotedSnapshotView.as_view()),
    path('voting-snapshot/top-volume/', TopVolumeSnapshotView.as_view()),
]
