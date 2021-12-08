from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from aqua_voting_tracker.utils.drf.filters import MultiGetFilterBackend
from aqua_voting_tracker.voting.models import VotingSnapshot
from aqua_voting_tracker.voting.pagination import FakePagination, VotingSnapshotPagination
from aqua_voting_tracker.voting.serializers import VotingSnapshotSerializer, VotingSnapshotStatsSerializer


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
    pagination_class = VotingSnapshotPagination

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class VotingSnapshotStatsView(BaseVotingSnapshotView):
    def get(self, request, *args, **kwargs):
        stats = VotingSnapshot.objects.current_stats()
        serializer = VotingSnapshotStatsSerializer(instance=stats, context=self.get_serializer_context())
        return Response(
            serializer.data,
        )
