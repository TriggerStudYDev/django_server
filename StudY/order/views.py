from django.db.models import Prefetch, Count
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from server.models import Faculty, Department
from .serializers import ProfileDisciplineSerializer, DisciplineSerializer
from functools import partial
from rest_framework.permissions import IsAuthenticated
from server.decorators import IsRole, IsVerified
from server.models import *


class DisciplinePagination(PageNumberPagination):
    """Пагинация для списка дисциплин (по 15 штук на кафедру)."""
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderDisciplinesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileDisciplineSerializer
    pagination_class = DisciplinePagination

    def get_queryset(self):
        user = self.request.user
        profile = get_object_or_404(Profile, user=user)

        # Получаем параметр flat (если передан, то приводим к bool)
        flat = self.request.query_params.get("flat", "false").lower() == "true"

        # Основной фильтр: выбираем кафедры факультета пользователя
        departments = Department.objects.filter(faculty=profile.faculty)

        # Фильтр по кафедрам (если переданы конкретные ID)
        department_ids = self.request.query_params.getlist("department_ids")
        if department_ids:
            departments = departments.filter(id__in=department_ids)

        # Базовый QuerySet для дисциплин
        disciplines_queryset = Discipline.objects.filter(department__faculty=profile.faculty)

        count_executor = self.request.query_params.getlist("count_executor")
        if count_executor:
            disciplines_queryset = disciplines_queryset.annotate(executor_count=Count("executordiscipline")).filter(executor_count__gt=0)

        # Фильтр по названию дисциплины
        search_query = self.request.query_params.get("search", "").strip()
        if search_query:
            disciplines_queryset = disciplines_queryset.filter(name__icontains=search_query)

        if flat:
            # Если flat=True → отдаем плоский список дисциплин
            return disciplines_queryset.order_by("id")

        # Prefetch дисциплин, ограничивая их количеством (до 15 на кафедру)
        disciplines_prefetch = Prefetch(
            "discipline_set",
            queryset=disciplines_queryset.order_by("id")[:15],  # Ограничиваем до 15 дисциплин
            to_attr="disciplines"
        )

        return departments.prefetch_related(disciplines_prefetch)

    def list(self, request, *args, **kwargs):
        """Переопределяем list() для поддержки двух вариантов вывода (группировка по кафедрам или плоский список)."""
        flat = self.request.query_params.get("flat", "false").lower() == "true"
        queryset = self.get_queryset()

        if flat:
            # Если `flat=True`, возвращаем список дисциплин
            page = self.paginate_queryset(queryset)
            serializer = DisciplineSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Если `flat=False`, возвращаем список кафедр с дисциплинами
        page = self.paginate_queryset(queryset)
        serializer = ProfileDisciplineSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)