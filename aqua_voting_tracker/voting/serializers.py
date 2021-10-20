from rest_framework import serializers

from aqua_voting_tracker.voting.models import VotingSnapshot


class VotingSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingSnapshot
        fields = ['market_key', 'rank', 'votes_value', 'voting_amount', 'timestamp']
