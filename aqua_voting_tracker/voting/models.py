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
                | models.Q(claimed_back_at__gt=time_filter)
            )
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
    def create_for_timestamp(self, timestamp, vote_queryset=None):
        if vote_queryset is None:
            vote_queryset = Vote.objects.all()

        vote_stats = vote_queryset.filter_exist_at(timestamp).values('market_key').annotate(
            votes_value=models.Sum('amount'),
            voting_amount=models.Count('voting_account', distinct=True),
        )

        snapshot_list = []
        vote_stats = sorted(vote_stats, key=lambda v: v['votes_value'], reverse=True)
        for index, vote in enumerate(vote_stats):
            snapshot_list.append(
                self.model(
                    market_key=vote['market_key'],
                    rank=index + 1,
                    votes_value=vote['votes_value'],
                    voting_amount=vote['voting_amount'],
                    timestamp=timestamp,
                ),
            )

        self.bulk_create(snapshot_list)

        return snapshot_list

    def filter_last_snapshot(self):
        last_snapshot_timestamp = self.order_by('-timestamp').values('timestamp')[:1]
        return self.filter(timestamp=models.Subquery(last_snapshot_timestamp))


class VotingSnapshot(models.Model):
    market_key = models.CharField(max_length=56)
    rank = models.PositiveIntegerField()

    votes_value = models.DecimalField(max_digits=20, decimal_places=7)
    voting_amount = models.PositiveIntegerField()

    timestamp = models.DateTimeField()

    objects = VotingSnapshotManager()

    def __str__(self):
        return f'{self.market_key} - {self.timestamp}'
