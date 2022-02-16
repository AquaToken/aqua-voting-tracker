from rest_framework.pagination import BasePagination, PageNumberPagination
from rest_framework.response import Response


class BaseVotingPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 200


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
