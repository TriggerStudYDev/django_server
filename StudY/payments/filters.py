import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    transaction_type = django_filters.ChoiceFilter(choices=Transaction.TRANSACTION_TYPES)
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')  # Больше или равно
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')  # Меньше или равно
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')  # Дата с
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')  # Дата по

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'created_at']  # Указываем поля для фильтрации


class TransactionForFinanceFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(field_name='profile__user__username', lookup_expr='icontains', label='По имени пользователя')
    transaction_type = django_filters.ChoiceFilter(choices=Transaction.TRANSACTION_TYPES, label='Тип транзакции')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte', label='Минимальная сумма')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte', label='Максимальная сумма')
    date_min = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='Дата с')
    date_max = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='Дата по')

    class Meta:
        model = Transaction
        fields = ['username', 'transaction_type', 'amount_min', 'amount_max', 'date_min', 'date_max']

