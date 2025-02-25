from django.db import models
from django.db.models import Avg

from server.models import Profile, Discipline


class Order(models.Model):
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    STATUS_CHOICES = [
        ('under_review', 'На рассмотрении'),
        ('changing_conditions', 'Изменение условий'),
        ('not_accepted_executor', 'Не принят исполнителем'),
        ('accepted_executor', 'Принят исполнителем'),
        ('accepted_customer', 'Принят заказчиком'),
        ('not_accepted_customer', 'Не принят заказчиком'),
        ('in_progress', 'В работе'),
        ('sent_for_revision', 'Отправлен на доработку'),
        ('guaranteed_flight', 'Гарантированный переиод'),
        ('completed', 'Завершен'),
        ('rejected_executor', 'Отклонен исполнителем'),
        ('rejected_customer', 'Отклонен заказчиком')
    ]

    TYPE_CHOICES = [
        ('lecture', 'Лекция'),
        ('practical', 'Практика'),
        ('lab_work', 'Лабораторная'),
        ('coursework', 'Курсовая'),
        ('thesis', 'Диплом'),
        ('other', 'Другое'),
    ]

    TYPE_ORDER = [
        ('public', 'Публичный'),
        ('personal', 'Персональный')
    ]

    customer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='orders', verbose_name='Заказчик'
    )
    performer = models.ForeignKey(
        Profile, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='assigned_orders', verbose_name='Исполнитель'
    )
    type = models.CharField(verbose_name='Тип заказа', max_length=30, choices=TYPE_ORDER, default='personal')
    discipline = models.ForeignKey('ExecutorDiscipline', verbose_name='Дисциплина', on_delete=models.PROTECT,
                                   null=True, blank=True)
    subject = models.ForeignKey(Discipline, verbose_name='Предмет', on_delete=models.PROTECT,
                                null=True, blank=True)
    title = models.CharField(verbose_name='Название заказа', max_length=255)
    type_order = models.CharField(verbose_name='Тип заказа', max_length=40, choices=TYPE_CHOICES)
    description = models.TextField(verbose_name='Описание заказа')
    file = models.FileField(
        verbose_name='Приложение', upload_to='order/annex_order/%Y/%m/%d/', blank=True, null=True
    )
    cost = models.DecimalField(verbose_name='Стоимость', max_digits=10, decimal_places=2)
    status = models.CharField(
        verbose_name='Статус заказа', max_length=30, choices=STATUS_CHOICES, default='under_review'
    )
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    last_modified_at = models.DateTimeField(verbose_name='Дата последнего изменения', auto_now=True)
    deadlines = models.DateTimeField(verbose_name='Дедлайн')
    warranty_period_until = models.DateTimeField(verbose_name='Гарантийный период до', null=True, blank=True)
    is_urgently = models.BooleanField(verbose_name='Срочный заказ?', default=False)

    def __str__(self):
        return f'Заказ {self.title} ({self.status})'


class OrderAdditionComment(models.Model):
    class Meta:
        verbose_name = 'Дополнение к заказу'
        verbose_name_plural = 'Дополнения к заказам'

    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.PROTECT)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    file = models.FileField(verbose_name='Файл', upload_to='order/additionComment/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)


class OrderResult(models.Model):
    class Meta:
        verbose_name = 'Результат работы'
        verbose_name_plural = 'Результат работ'

    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.PROTECT)
    description = models.TextField(verbose_name='Описание', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)


class OrderResultFile(models.Model):
    class Meta:
        verbose_name = 'Файл результата'
        verbose_name_plural = 'Файлы результатов'

    order_result = models.ForeignKey(OrderResult, verbose_name='Результат работы', on_delete=models.CASCADE)
    file = models.FileField(verbose_name='Файл', upload_to='order/results/%Y/%m/%d/')
    created_at = models.DateTimeField(verbose_name='Дата загрузки', auto_now_add=True)


class OrderComment(models.Model):
    """Комментарии к заказу"""
    class Meta:
        verbose_name = 'Комментарий к заказу'
        verbose_name_plural = 'Комментарии к заказам'

    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(Profile, verbose_name='Автор', on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата последнего изменения', auto_now=True)

    def __str__(self):
        return f'Комментарий от {self.user} для заказа {self.order.id}'


class OrderRating(models.Model):
    """Связь между заказом и пользователями для оценки"""
    class Meta:
        verbose_name = 'Оценка заказа'
        verbose_name_plural = 'Оценки заказов'
        unique_together = ('order', 'rated_by')

    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE, related_name='ratings')
    rated_by = models.ForeignKey(Profile, verbose_name='Кто оценил', on_delete=models.CASCADE, related_name='given_ratings')
    rated_to = models.ForeignKey(Profile, verbose_name='Кому поставлена оценка', on_delete=models.CASCADE, related_name='received_ratings')
    comment = models.TextField(verbose_name='Отзыв', null=True, blank=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)

    @property
    def overall_rating(self):
        avg_rating = self.criteria.aggregate(avg=Avg('value'))['avg']
        return round(avg_rating, 2) if avg_rating is not None else None

    def __str__(self):
        return f'Оценка {self.rated_to} по заказу {self.order.id}'


class OrderRatingCriteria(models.Model):
    """Оценки по отдельным критериям"""
    class Meta:
        verbose_name = 'Критерий оценки'
        verbose_name_plural = 'Критерии оценки'
        unique_together = ('rating', 'criterion')

    CRITERIA_CHOICES = [
        ('quality', 'Качество работы'),
        ('cost', 'Соотношение цены'),
        ('timing', 'Соблюдение сроков'),
    ]

    rating = models.ForeignKey(OrderRating, verbose_name='Оценка заказа', on_delete=models.CASCADE, related_name='criteria')
    criterion = models.CharField(verbose_name='Критерий', max_length=20, choices=CRITERIA_CHOICES)
    value = models.PositiveSmallIntegerField(verbose_name='Оценка', choices=[(i, str(i)) for i in range(1, 6)])

    def __str__(self):
        return f'{self.get_criterion_display()} - {self.value}'


class ExecutorDiscipline(models.Model):
    """Настройки дисциплин для исполнителя"""
    class Meta:
        verbose_name = 'Дисциплина исполнителя'
        verbose_name_plural = 'Дисциплины исполнителей'
        unique_together = ('executor', 'discipline')

    executor = models.ForeignKey(Profile, verbose_name='Исполнитель', on_delete=models.CASCADE,
                                 related_name='executor_disciplines')
    discipline = models.ForeignKey(Discipline, verbose_name='Дисциплина', on_delete=models.CASCADE)
    description = models.TextField(verbose_name='Описание')
    min_price = models.DecimalField(verbose_name='Минимальная цена', max_digits=10, decimal_places=2)
    max_price = models.DecimalField(verbose_name='Максимальная цена', max_digits=10, decimal_places=2)
    preferred_price = models.DecimalField(verbose_name='Желаемая цена', max_digits=10, decimal_places=2, null=True, blank=True)
    avg_time = models.PositiveIntegerField(verbose_name='Средний срок выполнения (дней)')
    guarantee_period = models.PositiveIntegerField(verbose_name='Гарантийный период (дней)')
    is_active = models.BooleanField(verbose_name='Активно', default=True)

    def get_overall_rating(self):
        # Вычисление общего рейтинга исполнителя на основе всех его заказов
        ratings = OrderRating.objects.filter(
            order__performer=self.executor,
        )
        overall_rating = ratings.aggregate(avg=Avg('criteria__value'))['avg']
        return round(overall_rating, 2) if overall_rating else None

    def get_discipline_rating(self):
        # Вычисление рейтинга по дисциплине
        orders = Order.objects.filter(
            performer=self.executor,
            discipline=self.discipline
        )

        if orders.count() < 3:
            return None  # Возвращаем null, если заказов менее 3

        ratings = OrderRating.objects.filter(
            order__performer=self.executor,
            order__discipline=self.discipline
        )
        discipline_rating = ratings.aggregate(avg=Avg('criteria__value'))['avg']
        return round(discipline_rating, 2) if discipline_rating else None

    def get_comments(self):
        # Получение всех комментариев для данной дисциплины
        orders = Order.objects.filter(
            performer=self.executor,
            discipline=self.discipline
        )

        ratings = OrderRating.objects.filter(
            order__in=orders
        )

        comments = ratings.values('rated_by', 'comment', 'created_at')
        return comments
    def __str__(self):
        return f'{self.executor} - {self.discipline.name}'


class OrderStatusLog(models.Model):
    class Meta:
        verbose_name = 'Лог статуса заказа'
        verbose_name_plural = 'Логи статусов заказов'

    STATUS_CHOICES = [
        ('under_review', 'На рассмотрении'),
        ('changing_conditions', 'Изменение условий'),
        ('not_accepted_executor', 'Не принят исполнителем'),
        ('not_accepted_customer', 'Не принят заказчиком'),
        ('accepted_executor', 'Принят исполнителем'),
        ('accepted_customer', 'Принят заказчиком'),
        ('in_progress', 'В работе'),
        ('sent_for_revision', 'Отправлен на доработку'),
        ('guaranteed_flight', 'Гарантированный переиод'),
        ('completed', 'Завершен'),
        ('rejected_executor', 'Отклонен исполнителем'),
        ('rejected_customer', 'Отклонен заказчиком')
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs', verbose_name='Заказ')
    status = models.CharField(verbose_name='Статус', max_length=50, choices=STATUS_CHOICES)
    date_changed = models.DateTimeField(verbose_name='Дата изменения', auto_now_add=True)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)

    def __str__(self):
        return f'Лог статуса для заказа {self.order.title} ({self.status})'


