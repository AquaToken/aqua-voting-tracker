from django.db import models


class VoteQuerySet(models.QuerySet):
    def filter_lock_at(self, time_filter):
        return self.filter(locked_at__lte=time_filter, locked_until__gt=time_filter)

    def filter_by_min_term(self, min_term):
        return self.annotate(term=models.F('locked_until') - models.F('locked_at')).filter(term__gte=min_term)

    def filter_exist_at(self, time_filter):
        return self.filter(
            models.Q(locked_at__lte=time_filter)
            & models.Q(
                models.Q(claimed_back_at__isnull=True)
                | models.Q(claimed_back_at__gt=time_filter),
            ),
        )

    def annotate_stats(self):
        return self.values('market_key').annotate(
            votes_value=models.Sum('amount'),
            voting_amount=models.Count('voting_account', distinct=True),
        )


class Vote(models.Model):
    balance_id = models.CharField(max_length=72, unique=True)

    voting_account = models.CharField(max_length=56)
    market_key = models.CharField(max_length=56)

    amount = models.DecimalField(max_digits=20, decimal_places=7)

    locked_at = models.DateTimeField()
    locked_until = models.DateTimeField()
    claimed_back_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = VoteQuerySet.as_manager()

    def __str__(self):
        return f'{self.market_key} - {self.amount}'

    def get_vote_term(self):
        return self.locked_until - self.locked_at


class VotingSnapshotManager(models.Manager):
    def filter_last_snapshot(self):
        last_snapshot_timestamp = self.order_by('-timestamp').values('timestamp')[:1]
        return self.filter(timestamp=models.Subquery(last_snapshot_timestamp))

    def current_stats(self):
        return self.filter_last_snapshot().aggregate(
            market_key_count=models.Count('market_key'),
            votes_value_sum=models.Sum(models.F('upvote_value') + models.F('downvote_value')),
            voting_amount_sum=models.Sum('voting_amount'),
            timestamp=models.Max('timestamp'),
        )


class VotingSnapshot(models.Model):
    market_key = models.CharField(max_length=56, db_index=True)
    rank = models.PositiveIntegerField()

    votes_value = models.DecimalField(max_digits=20, decimal_places=7)
    voting_amount = models.PositiveIntegerField()

    upvote_value = models.DecimalField(max_digits=20, decimal_places=7)
    downvote_value = models.DecimalField(max_digits=20, decimal_places=7)

    timestamp = models.DateTimeField(db_index=True)

    objects = VotingSnapshotManager()

    def __str__(self):
        return f'{self.market_key} - {self.timestamp}'
