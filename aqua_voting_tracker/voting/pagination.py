from rest_framework.pagination import BasePagination, CursorPagination
from rest_framework.response import Response


class VotingSnapshotCursorPagination(CursorPagination):
    ordering = 'rank'
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 200


class FakePagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        return queryset

    def get_paginated_response(self, data):
        return Response({
            'next': None,
            'previous': None,
            'results': data,
        })
