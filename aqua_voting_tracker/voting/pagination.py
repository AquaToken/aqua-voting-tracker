from rest_framework.pagination import BasePagination, CursorPagination
from rest_framework.response import Response


class VotingSnapshotCursorPagination(CursorPagination):
    ordering = NotImplemented
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 200

    def get_count(self, queryset):
        """
        Determine an object count, supporting either querysets or regular lists.
        """
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)

    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(queryset)
        return super(VotingSnapshotCursorPagination, self).paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


class FakePagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        return queryset

    def get_paginated_response(self, data):
        return Response({
            'count': len(data),
            'next': None,
            'previous': None,
            'results': data,
        })
