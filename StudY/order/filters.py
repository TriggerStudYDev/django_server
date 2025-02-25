import django_filters
from .models import Order
from django.utils.timezone import now


class OrderFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(field_name='type', lookup_expr='iexact')
    type_order = django_filters.CharFilter(field_name='type_order', lookup_expr='iexact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    is_urgently = django_filters.BooleanFilter(field_name='is_urgently')

    created_at_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    search = django_filters.CharFilter(method="filter_search")
    overdue = django_filters.BooleanFilter(method="filter_overdue")

    class Meta:
        model = Order
        fields = ['type', 'type_order', 'status', 'is_urgently']

    def filter_search(self, queryset, name, value):
        """Поиск по названию и описанию"""
        return queryset.filter(title__icontains=value) | queryset.filter(description__icontains=value)

    def filter_overdue(self, queryset, name, value):
        """Фильтр просроченных заказов (дедлайн прошел, а заказ не завершен)"""
        if value:
            return queryset.filter(
                deadlines__lt=now(),
                status__in=['in_progress', 'sent_for_revision']
            )
        return queryset

