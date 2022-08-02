from rest_framework import serializers

from aqua_voting_tracker.voting.models import VotingSnapshot


class VotingSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingSnapshot
        fields = ['market_key', 'rank', 'votes_value', 'voting_amount', 'adjusted_votes_value',
                  'upvote_value', 'downvote_value', 'extra', 'timestamp']


class VotingSnapshotStatsSerializer(serializers.Serializer):
    market_key_count = serializers.IntegerField()
    votes_value_sum = serializers.DecimalField(max_digits=20, decimal_places=7)
    voting_amount_sum = serializers.IntegerField()
    adjusted_votes_value_sum = serializers.DecimalField(max_digits=20, decimal_places=7)
    timestamp = serializers.DateTimeField()


class VotingAccountStatsSerializer(serializers.Serializer):
    voting_account = serializers.CharField()
    votes_value = serializers.DecimalField(max_digits=20, decimal_places=7)
