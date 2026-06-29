from datetime import datetime

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.exceptions import ParseError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from aqua_voting_tracker.utils.drf.filters import MultiGetFilterBackend
from aqua_voting_tracker.voting.models import Vote, VotingSnapshot
from aqua_voting_tracker.voting.pagination import BaseVotingPagination, FakePagination
from aqua_voting_tracker.voting.serializers import (
    VotingAccountStatsSerializer,
    VotingSnapshotSerializer,
    VotingSnapshotStatsSerializer,
)


class BaseVotingSnapshotView(GenericAPIView):
    serializer_class = VotingSnapshotSerializer
    queryset = VotingSnapshot.objects.filter_last_snapshot().annotate_assets()
    permission_classes = (AllowAny, )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['whitelisted_for_rewards']


class MultiGetVotingSnapshotView(ListModelMixin, BaseVotingSnapshotView):
    pagination_class = FakePagination
    filter_backends = [MultiGetFilterBackend, DjangoFilterBackend]
    multiget_filter_fields = ['market_key']

    def get_queryset(self):
        queryset = super().get_queryset()

        if not any(filter_field in self.request.query_params for filter_field in self.multiget_filter_fields):
            return queryset.none()

        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class VotingSnapshotListView(ListModelMixin, BaseVotingSnapshotView):
    """
    Paginated list of the latest voting snapshot rows.

    Supports ordering via the ``?ordering=`` query param. Prefix a field with
    ``-`` for descending order and pass several comma-separated fields to sort
    by more than one column, e.g. ``?ordering=-adjusted_votes_value,-votes_value``.
    Only the fields listed in ``ordering_fields`` are allowed; unknown fields are
    silently ignored.
    """
    pagination_class = BaseVotingPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        'rank',
        'votes_value',
        'voting_amount',
        'upvote_value',
        'downvote_value',
        'adjusted_votes_value',
        'timestamp',
    ]
    # Default ordering applied when ``?ordering=`` is not provided.
    ordering = ['-adjusted_votes_value', '-votes_value']

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class TopVolumeSnapshotView(VotingSnapshotListView):
    """Deprecated alias of ``VotingSnapshotListView`` sorted by volume by default."""
    ordering = ['-adjusted_votes_value', '-votes_value']


class TopVotedSnapshotView(VotingSnapshotListView):
    """Deprecated alias of ``VotingSnapshotListView`` sorted by voting amount by default."""
    ordering = ['-voting_amount']


class VotingSnapshotStatsView(BaseVotingSnapshotView):
    def get(self, request, *args, **kwargs):
        stats = VotingSnapshot.objects.filter_last_snapshot().current_stats()
        serializer = VotingSnapshotStatsSerializer(instance=stats, context=self.get_serializer_context())
        return Response(
            serializer.data,
        )


class VotingAccountStatsView(ListModelMixin, GenericAPIView):
    serializer_class = VotingAccountStatsSerializer
    permission_classes = (AllowAny, )
    pagination_class = BaseVotingPagination

    timestamp_param = 'timestamp'

    def get_queryset(self):
        timestamp = self.request.query_params.get(self.timestamp_param)
        try:
            timestamp = datetime.utcfromtimestamp(int(timestamp)).replace(tzinfo=timezone.utc)
        except (ValueError, OverflowError):
            raise ParseError()

        return Vote.objects.filter(
            market_key=self.kwargs.get('market_key', ''),
        ).filter_exist_at(
            timestamp,
        # ).filter_by_min_term(
        #     settings.VOTING_MIN_TERM,
        ).annotate_by_voting_account().order_by('voting_account')

    def injection_timestamp(self):
        """
        Insert current timestamp into query params. It needed to avoid timestamp shifting at pagination.
        """
        query_string = self.request._request.META.get('QUERY_STRING')
        if f'{self.timestamp_param}=' in query_string:
            return

        now = int(timezone.now().timestamp())
        if query_string:
            query_string += '&'
        query_string += f'{self.timestamp_param}={now}'

        self.request._request.META['QUERY_STRING'] = query_string
        self.request.query_params._mutable = True
        self.request.query_params['timestamp'] = now
        self.request.query_params._mutable = False

    def get(self, request, *args, **kwargs):
        self.injection_timestamp()
        return self.list(request, *args, **kwargs)
