from django.contrib import admin

from aqua_voting_tracker.voting.models import Vote, VotingSnapshot


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voting_account', 'market_key', 'amount', 'locked_at', 'locked_until']
    readonly_fields = ['balance_id', 'voting_account', 'market_key', 'amount', 'locked_at', 'locked_until']


@admin.register(VotingSnapshot)
class VotingSnapshotAdmin(admin.ModelAdmin):
    list_display = ['market_key', 'rank', 'timestamp', 'votes_value', 'voting_amount']
    readonly_fields = ['market_key', 'rank', 'timestamp', 'votes_value', 'voting_amount']
    ordering = ['-timestamp', 'rank']
