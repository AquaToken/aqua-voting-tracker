from datetime import datetime

from django.conf import settings
from django.utils import timezone

from rest_framework.exceptions import ParseError
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
    queryset = VotingSnapshot.objects.filter_last_snapshot()
    permission_classes = (AllowAny, )


class MultiGetVotingSnapshotView(ListModelMixin, BaseVotingSnapshotView):
    pagination_class = FakePagination
    filter_backends = [MultiGetFilterBackend]
    multiget_filter_fields = ['market_key']

    def get_queryset(self):
        queryset = super(MultiGetVotingSnapshotView, self).get_queryset()

        if not any(filter_field in self.request.query_params for filter_field in self.multiget_filter_fields):
            return queryset.none()

        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class TopVolumeSnapshotView(ListModelMixin, BaseVotingSnapshotView):
    queryset = BaseVotingSnapshotView.queryset.order_by('-votes_value')
    pagination_class = BaseVotingPagination

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class VotingSnapshotStatsView(BaseVotingSnapshotView):
    def get(self, request, *args, **kwargs):
        stats = VotingSnapshot.objects.current_stats()
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
            market_key=self.request.kwargs.get('market_key', ''),
        ).filter_exist_at(
            timestamp,
        ).filter_by_min_term(
            settings.VOTING_MIN_TERM,
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
