from django.utils.timezone import now
from rest_framework import serializers
from .models import *
from server.models import Discipline, Department
# import magic


class DisciplineSerializer(serializers.ModelSerializer):
    executor_count = serializers.SerializerMethodField()

    class Meta:
        model = Discipline
        fields = ['id', 'name', 'photo', 'executor_count']

    def get_executor_count(self, obj):
        return ExecutorDiscipline.objects.filter(discipline=obj).count()


class ProfileDisciplineSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='name')
    department_photo = serializers.ImageField(source='photo')
    disciplines = DisciplineSerializer(many=True)

    class Meta:
        model = Department
        fields = ['id', 'department_name', 'department_photo', 'disciplines']


# class ExecutorDisciplineSerializer(serializers.ModelSerializer):
#     executor_name = serializers.CharField(source='executor.user.username')  # Имя исполнителя
#     discipline_name = serializers.CharField(source='discipline.name')  # Название дисциплины
#
#     class Meta:
#         model = ExecutorDiscipline
#         fields = ['id', 'executor_name', 'discipline_name', 'description', 'min_price', 'max_price', 'preferred_price', 'avg_time', 'guarantee_period', 'is_active']
#


class ExecutorDisciplineSerializer(serializers.ModelSerializer):
    executor_id = serializers.IntegerField(source='executor.id', read_only=True)
    username = serializers.CharField(source='executor.user.username', read_only=True)
    photo = serializers.ImageField(source='executor.photo', read_only=True)
    overall_rating = serializers.SerializerMethodField()
    discipline_rating = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = ExecutorDiscipline
        fields = [
            'id', 'executor_id', 'username', 'photo', 'discipline', 'description', 'min_price', 'max_price',
            'preferred_price', 'avg_time', 'guarantee_period', 'is_active', 'overall_rating', 'discipline_rating', 'comments'
        ]

    def get_overall_rating(self, obj):
        """Средний рейтинг исполнителя по всем заказам"""
        ratings = OrderRating.objects.filter(rated_to=obj.executor)
        avg_rating = ratings.aggregate(Avg('criteria__value'))['criteria__value__avg']
        return round(avg_rating, 2) if avg_rating is not None else None

    def get_discipline_rating(self, obj):
        """Средний рейтинг исполнителя по конкретной дисциплине (если есть ≥ 3 заказа)"""
        orders = Order.objects.filter(performer=obj.executor, discipline=obj)
        if orders.count() < 3:
            return None  # Если заказов меньше 3, рейтинг не учитывается
        ratings = OrderRating.objects.filter(order__in=orders, rated_to=obj.executor)
        avg_rating = ratings.aggregate(Avg('criteria__value'))['criteria__value__avg']
        return round(avg_rating, 2) if avg_rating is not None else None

    def get_comments(self, obj):
        """Получение отзывов по данной дисциплине"""
        orders = Order.objects.filter(performer=obj.executor, discipline=obj)
        comments = OrderRating.objects.filter(order__in=orders, rated_to=obj.executor).values('comment', 'created_at')
        return list(comments)


class DisciplineSerializer(serializers.ModelSerializer):
    """Сериализатор для дисциплин, если они не созданы как ExecutorDiscipline"""
    department = serializers.CharField(source='department.name')
    faculty = serializers.CharField(source='department.faculty.name')
    university = serializers.CharField(source='department.faculty.university.name')

    class Meta:
        model = Discipline
        fields = ["id", "name", "department", "faculty", "university"]


class ExecutorSelfDisciplineSerializer(serializers.ModelSerializer):
    """Сериализатор для дисциплин исполнителя"""
    discipline_rating = serializers.SerializerMethodField()

    class Meta:
        model = ExecutorDiscipline
        fields = "__all__"

    def get_discipline_rating(self, obj):
        return obj.get_discipline_rating()


class ExecutorDisciplineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutorDiscipline
        fields = ['executor', 'discipline', 'description', 'min_price', 'max_price',
                  'preferred_price', 'avg_time', 'guarantee_period', 'is_active']


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['discipline', 'title', 'type_order', 'description', 'file', 'cost', 'deadlines',
                  'warranty_period_until', 'is_urgently']

    def validate_discipline(self, value):
        """
        Проверка дисциплины: должна существовать и быть активной.
        """
        if not ExecutorDiscipline.objects.filter(id=value.id, is_active=True).exists():
            raise serializers.ValidationError("Выбранная дисциплина неактивна или не существует.")
        return value

    def validate_cost(self, value):
        """
        Проверяем, что стоимость заказа входит в диапазон min_price - max_price исполнителя.
        """
        discipline = self.initial_data.get('discipline')
        if not discipline:
            raise serializers.ValidationError("Дисциплина не указана.")

        try:
            discipline = ExecutorDiscipline.objects.get(id=discipline)
        except ExecutorDiscipline.DoesNotExist:
            raise serializers.ValidationError("Дисциплина не найдена.")

        if not (discipline.min_price <= value <= discipline.max_price):
            raise serializers.ValidationError(
                f"Стоимость должна быть в диапазоне от {discipline.min_price} до {discipline.max_price}."
            )
        return value

    def validate_deadlines(self, value):
        """
        Проверяем, что дедлайн не находится в прошлом.
        """
        if value < now():
            raise serializers.ValidationError("Дедлайн не может быть в прошлом.")
        return value

    def validate_warranty_period_until(self, value):
        """
        Проверяем, что гарантийный период больше, чем дедлайн.
        """
        deadlines = self.initial_data.get('deadlines')
        if not deadlines:
            raise serializers.ValidationError("Дедлайн должен быть указан.")

        if isinstance(deadlines, str):
            try:
                deadlines = serializers.DateTimeField().to_internal_value(deadlines)
            except serializers.ValidationError:
                raise serializers.ValidationError("Неверный формат даты для дедлайна.")

        if value <= deadlines:
            raise serializers.ValidationError("Гарантийный период должен быть позже дедлайна.")
        return value

    def validate_file(self, file):
        """
        Проверка загружаемого файла:
        - Разрешенные форматы: pdf, docx.
        - Размер не более 110 МБ.
        """
        if not file:
            return file  # Файл не является обязательным полем

        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        # file_type = magic.from_buffer(file.read(2048), mime=True)  # Читаем первые 2048 байт файла
        #
        # if file_type not in allowed_types:
        #     raise serializers.ValidationError("Разрешены только файлы PDF и DOCX.")

        if file.size > 110 * 1024 * 1024:  # 110 МБ
            raise serializers.ValidationError("Размер файла не должен превышать 110 МБ.")

        return file

    def create(self, validated_data):
        """
        Создание заказа с автоматическим статусом и логированием.
        """
        discipline = validated_data['discipline']

        validated_data['status'] = 'under_review'  # Автоматически устанавливаем статус "На рассмотрении"
        validated_data['performer'] = discipline.executor  # Исполнитель = владелец дисциплины
        order = Order.objects.create(**validated_data)

        # Записываем лог статуса
        OrderStatusLog.objects.create(order=order, status='under_review', comment='Заказ создан')

        return order



class OrderAdditionCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAdditionComment
        fields = ['id', 'description', 'file', 'created_at']


class OrderResultFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderResultFile
        fields = ['id', 'file', 'created_at']


class OrderResultSerializer(serializers.ModelSerializer):
    result_files = OrderResultFileSerializer(many=True, source='orderresultfile_set')

    class Meta:
        model = OrderResult
        fields = ['id', 'description', 'created_at', 'result_files']


class OrderCommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')  # Вывод имени пользователя

    class Meta:
        model = OrderComment
        fields = ['id', 'user', 'text', 'created_at', 'updated_at']


class OrderRatingCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderRatingCriteria
        fields = ['criterion', 'value']


class OrderRatingSerializer(serializers.ModelSerializer):
    rated_by = serializers.CharField(source='rated_by.username')
    rated_to = serializers.CharField(source='rated_to.username')
    overall_rating = serializers.FloatField()
    criteria = OrderRatingCriteriaSerializer(many=True)

    class Meta:
        model = OrderRating
        fields = ['id', 'rated_by', 'rated_to', 'comment', 'overall_rating', 'created_at', 'criteria']


class OrderStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusLog
        fields = ['id', 'status', 'date_changed', 'comment']


class OrderListSerializer(serializers.ModelSerializer):
    addition_comments = OrderAdditionCommentSerializer(many=True, source='orderadditioncomment_set')
    results = OrderResultSerializer(many=True, source='orderresult_set')
    comments = OrderCommentSerializer(many=True)
    ratings = OrderRatingSerializer(many=True)
    status_logs = OrderStatusLogSerializer(many=True)
    counterparty = serializers.SerializerMethodField()  # Добавляем вычисляемое поле

    class Meta:
        model = Order
        fields = [
            'id', 'title', 'type', 'type_order', 'description', 'cost', 'status',
            'created_at', 'deadlines', 'is_urgently', 'counterparty',
            'addition_comments', 'results', 'comments', 'ratings', 'status_logs'
        ]

    def get_counterparty(self, obj):
        """Определяет, кто является второй стороной сделки (заказчик или исполнитель)"""
        request_user = self.context['request'].user
        profile = Profile.objects.get(user=request_user)

        if profile == obj.customer:
            # Если текущий пользователь - заказчик, отдаем данные исполнителя
            counterparty = obj.performer
        else:
            # Если текущий пользователь - исполнитель, отдаем данные заказчика
            counterparty = obj.customer

        if not counterparty:
            return None  # Если исполнитель не назначен, возвращаем None

        return {
            'id': counterparty.id,
            'username': counterparty.user.username,
            'overall_rating': self.get_overall_rating(counterparty),
            'vk_link': counterparty.vk_profile,
            'tg_link': counterparty.telegram_username,
        }

    def get_overall_rating(self, profile):
        """Рассчитывает средний рейтинг пользователя по всем заказам"""
        overall_rating = profile.received_ratings.aggregate(avg=Avg('criteria__value'))['avg']
        return round(overall_rating, 2) if overall_rating is not None else None


class OrderActionSerializer(serializers.Serializer):
    """Сериализатор для принятия и отклонения заказа"""
    description = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField(required=False)


class OrderEditSerializer(serializers.ModelSerializer):
    """Сериализатор для редактирования заказа"""

    class Meta:
        model = Order
        fields = ['cost', 'deadlines', 'warranty_period_until']