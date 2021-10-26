from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny

from aqua_voting_tracker.utils.drf.filters import MultiGetFilterBackend
from aqua_voting_tracker.voting.models import VotingSnapshot
from aqua_voting_tracker.voting.pagination import FakePagination, VotingSnapshotCursorPagination
from aqua_voting_tracker.voting.serializers import VotingSnapshotSerializer


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


class TopVotingSnapshotView(ListModelMixin, BaseVotingSnapshotView):
    queryset = BaseVotingSnapshotView.queryset.order_by('rank')
    pagination_class = VotingSnapshotCursorPagination

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
