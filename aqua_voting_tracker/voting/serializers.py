from rest_framework import serializers

from aqua_voting_tracker.voting.models import VotingSnapshot


class VotingSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingSnapshot
        fields = ['market_key', 'rank', 'votes_value', 'voting_amount', 'upvote_value', 'downvote_value', 'timestamp']


class VotingSnapshotStatsSerializer(serializers.Serializer):
    market_key_count = serializers.IntegerField()
    votes_value_sum = serializers.DecimalField(max_digits=20, decimal_places=7)
    voting_amount_sum = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
