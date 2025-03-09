from django.db.models import Prefetch, Count
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OrderFilter

from .serializers import *
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
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)
                          ]
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

        disciplines_prefetch = Prefetch(
            "discipline_set",
            queryset=disciplines_queryset.order_by("id")[:2],  # Ограничиваем до n дисциплин
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

        page = self.paginate_queryset(queryset)
        serializer = ProfileDisciplineSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ExecutorDisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExecutorDisciplineSerializer
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['заказчик']),
        partial(IsVerified)
    ]

    def get_queryset(self):
        """Получение списка исполнителей по дисциплине"""
        discipline_id = self.request.query_params.get('discipline_id')

        if not discipline_id:
            return ExecutorDiscipline.objects.none()

        return ExecutorDiscipline.objects.filter(discipline_id=discipline_id, is_active=True)

    def list(self, request, *args, **kwargs):
        """Проверки перед выводом списка"""
        user = request.user.profile
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response({"error": "Нет исполнителей по указанной дисциплине"}, status=status.HTTP_404_NOT_FOUND)

        # Проверка факультета
        discipline_faculty = queryset.first().discipline.department.faculty
        if user.faculty != discipline_faculty:
            return Response({"error": "Вы не можете просматривать дисциплины другого факультета"}, status=status.HTTP_403_FORBIDDEN)

        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Получение информации о конкретном исполнителе в дисциплине с проверкой факультета"""
        user = request.user.profile
        discipline_id = request.query_params.get('discipline_id')
        executor_discipline_id = kwargs.get('pk')

        if not discipline_id:
            return Response({"error": "discipline_id не передан"}, status=status.HTTP_400_BAD_REQUEST)

        executor_discipline = get_object_or_404(ExecutorDiscipline, id=executor_discipline_id, discipline_id=discipline_id, is_active=True)

        # Проверка факультета
        if user.faculty != executor_discipline.discipline.department.faculty:
            return Response({"error": "Вы не можете просматривать дисциплины другого факультета"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(executor_discipline)
        return Response(serializer.data)


class ExecutorSelfDisciplineViewSet(ReadOnlyModelViewSet):
    """
    Выводит список дисциплин исполнителя:
    - Если дисциплина не имеет ExecutorDiscipline → выводим Discipline (с факультетом, кафедрой, университетом).
    - Если дисциплина уже есть в ExecutorDiscipline → выводим ее со всеми параметрами.
    """
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['исполнитель']),
        partial(IsVerified)
    ]

    def list(self, request, *args, **kwargs):
        # Получаем профиль текущего пользователя
        user_profile = Profile.objects.get(user=request.user)

        # Получаем все дисциплины пользователя
        user_disciplines = user_profile.disciplines.all()

        # Получаем дисциплины, которые уже зарегистрированы в ExecutorDiscipline
        executor_disciplines = ExecutorDiscipline.objects.filter(executor=user_profile)

        executor_discipline_map = {ed.discipline.id: ed for ed in executor_disciplines}
        response_data = []

        for discipline in user_disciplines:
            if discipline.id in executor_discipline_map:
                # Если дисциплина уже зарегистрирована в ExecutorDiscipline
                executor_discipline = executor_discipline_map[discipline.id]
                response_data.append({
                    "type": "executor_discipline",
                    "data": ExecutorDisciplineSerializer(executor_discipline).data
                })
            else:
                # Если дисциплина еще не создана, добавляем данные о Discipline
                response_data.append({
                    "type": "discipline",
                    "data": DisciplineSerializer(discipline).data
                })

        return Response(response_data)


class ExecutorDisciplineCreateView(APIView):
    """
    Создание дисциплины для исполнителя.
    Проверяется наличие дисциплины в профиле и отсутствие дисциплины для исполнителя.
    Также проверяется корректность стоимостей.
    """
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['исполнитель']),
        partial(IsVerified)
    ]

    def post(self, request, *args, **kwargs):
        # Получаем профиль пользователя
        user_profile = Profile.objects.get(user=request.user)

        # Получаем дисциплину, которую исполнитель хочет добавить
        discipline_id = request.data.get('discipline_id')

        try:
            discipline = Discipline.objects.get(id=discipline_id)
        except Discipline.DoesNotExist:
            raise NotFound(detail="Дисциплина с таким ID не найдена.")

        # Проверяем, есть ли данная дисциплина в профиле
        if discipline not in user_profile.disciplines.all():
            return Response({"detail": "Дисциплина не найдена в вашем профиле."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, есть ли уже дисциплина для исполнителя
        if ExecutorDiscipline.objects.filter(executor=user_profile, discipline=discipline).exists():
            return Response({"detail": "Дисциплина для исполнителя уже существует."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Получаем стоимости из запроса
        min_price_str = request.data.get('min_price')
        max_price_str = request.data.get('max_price')
        preferred_price_str = request.data.get('preferred_price')

        # Преобразуем строки в числа (float)
        try:
            min_price = float(min_price_str)
            max_price = float(max_price_str)
            preferred_price = float(preferred_price_str)
        except ValueError:
            return Response({"detail": "Все стоимости должны быть числовыми значениями."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, что минимальная стоимость меньше максимальной
        if min_price >= max_price:
            return Response({"detail": "Минимальная стоимость должна быть меньше максимальной."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, что желаемая стоимость в пределах диапазона
        if not (min_price <= preferred_price <= max_price):
            return Response({"detail": "Желаемая стоимость должна быть в пределах между минимальной и максимальной стоимостью."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Если все проверки прошли успешно, создаем новую дисциплину для исполнителя
        data = {
            'executor': user_profile.id,
            'discipline': discipline.id,
            'description': request.data.get('description'),
            'min_price': min_price,
            'max_price': max_price,
            'preferred_price': preferred_price,
            'avg_time': request.data.get('avg_time'),
            'guarantee_period': request.data.get('guarantee_period'),
            'is_active': request.data.get('is_active', True),
        }

        serializer = ExecutorDisciplineCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderPersonalCreateView(generics.CreateAPIView):

    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['заказчик']),
        partial(IsVerified)
    ]

    def perform_create(self, serializer):

        user = self.request.user
        profile = Profile.objects.get(user=user)
        serializer.save(customer=profile)


class ExecutorCustomerOrderViewSet(ReadOnlyModelViewSet):
    """
    API для просмотра заказов исполнителя или заказчика с фильтрацией
    """
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    def get_queryset(self):
        """
        Возвращает заказы:
        - Если пользователь является исполнителем → показывает заказы, где он назначен.
        - Если пользователь является заказчиком → показывает заказы, которые он создал.
        """
        user_profile = Profile.objects.get(user=self.request.user)

        return Order.objects.filter(
            performer=user_profile
        ).prefetch_related(
            'orderadditioncomment_set',
            'orderresult_set__orderresultfile_set',
            'comments',
            'ratings__criteria',
            'status_logs'
        ) | Order.objects.filter(
            customer=user_profile
        ).prefetch_related(
            'orderadditioncomment_set',
            'orderresult_set__orderresultfile_set',
            'comments',
            'ratings__criteria',
            'status_logs'
        )

class OrderExecutorActionsViewSet(ViewSet):
    """
    API для обработки заявок исполнителем:
    1. Принять заказ (`accept_order`)
    2. Отклонить заказ (`reject_order`)
    3. Изменить условия (`edit_order`)
    """
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['исполнитель']),
        partial(IsVerified)
    ]

    def get_order(self, order_id):
        """Получает заказ и проверяет, является ли текущий пользователь исполнителем."""
        order = get_object_or_404(Order, id=order_id)
        user_profile = get_object_or_404(Profile, user=self.request.user)

        if order.performer != user_profile:
            return None  # Исполнитель не совпадает
        return order

    def accept_order(self, request, order_id):
        """Исполнитель принимает заказ"""
        order = self.get_order(order_id)
        if not order:
            return Response({"error": "Вы не являетесь исполнителем данного заказа"}, status=status.HTTP_403_FORBIDDEN)

        if order.status != 'under_review':
            return Response({"error": "Заказ можно принять только в статусе 'На рассмотрении'"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderActionSerializer(data=request.data)
        if serializer.is_valid():
            # Изменяем статус заказа
            order.status = 'accepted_executor'
            order.save()

            # Записываем комментарий, если он есть
            description = serializer.validated_data.get("description")
            file = serializer.validated_data.get("file")

            if description or file:
                OrderAdditionComment.objects.create(
                    order=order,
                    description=description if description else None,
                    file=file if file else None
                )

            # Логируем статус
            OrderStatusLog.objects.create(
                order=order,
                status='accepted_executor',
                comment="Исполнитель принял работу"
            )

            return Response({"message": "Заказ принят исполнителем"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def reject_order(self, request, order_id):
        """Исполнитель отклоняет заказ"""
        order = self.get_order(order_id)
        if not order:
            return Response({"error": "Вы не являетесь исполнителем данного заказа"}, status=status.HTTP_403_FORBIDDEN)

        if order.status != 'under_review':
            return Response({"error": "Заказ можно отклонить только в статусе 'На рассмотрении'"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderActionSerializer(data=request.data)
        if serializer.is_valid():
            # Изменяем статус заказа
            order.status = 'not_accepted_customer'
            order.save()

            # Записываем комментарий, если он есть
            description = serializer.validated_data.get("description")
            file = serializer.validated_data.get("file")

            if description or file:
                OrderAdditionComment.objects.create(
                    order=order,
                    description=description if description else None,
                    file=file if file else None
                )

            # Логируем статус
            OrderStatusLog.objects.create(
                order=order,
                status='not_accepted_customer',
                comment="Исполнитель отклонил работу"
            )

            return Response({"message": "Заказ отклонен исполнителем"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def edit_order(self, request, order_id):
        """Исполнитель изменяет условия заказа"""
        order = self.get_order(order_id)
        if not order:
            return Response({"error": "Вы не являетесь исполнителем данного заказа"}, status=status.HTTP_403_FORBIDDEN)

        if order.status != 'under_review':
            return Response({"error": "Изменять условия заказа можно только в статусе 'На рассмотрении'"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что хотя бы одно из полей изменяется
        cost = request.data.get("cost")
        deadlines = request.data.get("deadlines")
        warranty_period_until = request.data.get("warranty_period_until")

        if not any([cost, deadlines, warranty_period_until]):
            return Response({"error": "Необходимо изменить хотя бы одно поле: cost, deadlines или warranty_period_until"},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderEditSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Обновляем статус заказа
            order.status = 'changing_conditions'
            order.save()

            # Логируем изменение условий
            OrderStatusLog.objects.create(
                order=order,
                status='changing_conditions',
                comment="Исполнитель изменил условия"
            )

            # Записываем дополнительный комментарий, если переданы данные
            description = request.data.get("description")
            file = request.data.get("file")

            if description or file:
                OrderAdditionComment.objects.create(
                    order=order,
                    description=description if description else None,
                    file=file if file else None
                )

            return Response({"message": "Условия заказа изменены исполнителем"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderCustomerActionsViewSet(ViewSet):
    """
    API для обработки действий заказчика:
    1. Подтвердить заказ (`confirm_order`)
    """
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['заказчик']),
        partial(IsVerified)
    ]

    def get_order(self, order_id):
        """Получает заказ и проверяет, является ли текущий пользователь заказчиком."""
        order = get_object_or_404(Order, id=order_id)
        user_profile = get_object_or_404(Profile, user=self.request.user)

        if order.customer != user_profile:
            return Response({'error': 'Вы не являетесь заказчиком этого заказа'}, status=403)
        return order

    def confirm_order(self, request, order_id):
        """
        Заказчик подтверждает или отклоняет измененные условия.
        Может сработать на статусах:
        - 'changing_conditions' (изменение условий)
        - 'accepted_executor' (принят исполнителем)
        """
        order = self.get_order(order_id)

        if order.status not in ['changing_conditions', 'accepted_executor']:
            return Response({'error': 'Заказ не находится в стадии подтверждения'}, status=400)

        decision = request.data.get('decision')  # 'accept' или 'reject'
        if decision == 'accept':
            order.status = 'in_progress'
            order.save(update_fields=['status'])
            OrderStatusLog.objects.create(
                order=order,
                status='accepted_customer',
                comment="Заказ принят заказчиком"
            )
            OrderStatusLog.objects.create(
                order=order,
                status='in_progress',
                comment="Заказ перешел на этап 'В работе'"
            )
            return Response({'message': 'Заказ запущен в работу', 'new_status': order.status})

        elif decision == 'reject':
            order.status = 'not_accepted_customer'
            order.save(update_fields=['status'])
            OrderStatusLog.objects.create(
                order=order,
                status='not_accepted_customer',
                comment="Заказ отменен заказчиком"
            )

            return Response({'message': 'Заказ отклонен заказчиком', 'new_status': order.status})

        else:
            return Response({'error': 'Некорректное решение. Ожидается "accept" или "reject".'}, status=400)