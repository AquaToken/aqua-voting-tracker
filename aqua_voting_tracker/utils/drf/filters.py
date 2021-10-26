from rest_framework.filters import BaseFilterBackend


class MultiGetFilterBackend(BaseFilterBackend):
    filter_fields_param = 'multiget_filter_fields'
    max_page_size = 200

    def get_filter_fields(self, view):
        return getattr(view, self.filter_fields_param, [])

    def filter_queryset(self, request, queryset, view):
        available_filter_fields = self.get_filter_fields(view)
        if not available_filter_fields:
            return queryset

        query_params = request.query_params
        filter_field = next((field for field in available_filter_fields if query_params.get(field)), None)
        if not filter_field:
            return queryset

        filter_value = query_params.getlist(filter_field)[:self.max_page_size]
        return queryset.filter(**{filter_field + '__in': filter_value})
