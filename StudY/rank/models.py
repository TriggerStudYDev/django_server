from django.db import models


class Rank(models.Model):
    RANK_TYPE_CHOICES = [
        ('customer', 'Заказчик'),
        ('executor', 'Исполнитель'),
    ]

    rank_name = models.CharField(max_length=255, verbose_name="Название ранга")
    rank_type = models.CharField(max_length=10, choices=RANK_TYPE_CHOICES, verbose_name="Тип ранга")
    rank_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена ранга")
    rank_image_url = models.ImageField(null=True, blank=True, verbose_name='Фотография',
                                       upload_to='rank/photo/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f'{self.rank_name} - {self.rank_type}'

    class Meta:
        verbose_name = "Ранг"
        verbose_name_plural = "Ранги"


class RankDescription(models.Model):
    PRIVILEGE_TYPE_CHOICES = [
        ('quantitative', 'Количественный'),
        ('unique', 'Уникальный'),
    ]

    rank = models.ForeignKey(Rank, related_name='descriptions', on_delete=models.CASCADE, verbose_name="Ранг")
    description_text = models.TextField(verbose_name="Описание привилегии")
    privilege_type = models.CharField(max_length=15, choices=PRIVILEGE_TYPE_CHOICES, verbose_name="Тип привилегии")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Описание для {self.rank.rank_name}"

    class Meta:
        verbose_name = "Описание ранга"
        verbose_name_plural = "Описания рангов"


class RankSettings(models.Model):
    class Meta:
        verbose_name = "Настройки ранга"
        verbose_name_plural = "Настройки рангов"

    type_role = models.CharField(verbose_name='Тип пользователя', max_length=20, choices=[('executer', 'исполнитель'),
                                                                                          ('customer', 'заказчик')])
    rank = models.OneToOneField(Rank, related_name="settings", on_delete=models.CASCADE, verbose_name="Ранг")

    # Количественные параметры (int)
    discount_internal_purchases = models.IntegerField(default=0, verbose_name="Скидка на внутренние покупки (%)")
    referral_bonus_self = models.IntegerField(default=0, verbose_name="Бонус за приглашенного пользователя (₽)")
    referral_bonus_invited = models.IntegerField(default=0, verbose_name="Бонус для приглашенного пользователя (₽)")
    discount_orders = models.IntegerField(default=0, verbose_name="Скидка на заказы (%)")
    commission_reduction = models.IntegerField(default=0, verbose_name="Снижение комиссии от заказа (%)")
    bonus_account_limit = models.IntegerField(default=0, verbose_name="Ограничения бонусного счета (₽)")

    # Уникальные привилегии (bool)
    notifications_to_executor = models.BooleanField(default=False, verbose_name="Уведомления исполнителю")
    market_price_stats = models.BooleanField(default=False, verbose_name="Вывод статистики рыночных цен")
    extra_discount_per_order = models.BooleanField(default=False, verbose_name="Дополнительная скидка после каждого заказа")
    visibility_other_universities = models.BooleanField(default=False, verbose_name="Видимость исполнителей из других университетов")
    bonus_to_fiat_transfer = models.BooleanField(default=False, verbose_name="Перевод бонусов в фиат")
    can_print = models.BooleanField(default=False, verbose_name="Возможность печатать")
    customer_unlimited_fiat_withdrawals = models.BooleanField(default=False,
                                                              verbose_name="Снятие с фиатного счета без ограничений")
    # Привилегии исполнителя (bool)
    monthly_contests = models.BooleanField(default=False, verbose_name="Участие в ежемесячных конкурсах")
    create_internal_courses = models.BooleanField(default=False, verbose_name="Доступ к созданию внутренних курсов")
    publish_articles = models.BooleanField(default=False, verbose_name="Публикация статей")
    upload_work_to_study = models.BooleanField(default=False, verbose_name="Загрузка успешных работ в справочник StudY")
    mandatory_review = models.BooleanField(default=False, verbose_name="Обязательный отзыв от заказчика")
    unlimited_fiat_withdrawals = models.BooleanField(default=False, verbose_name="Вывод фиатных средств без ограничений")
    executer_unlimited_fiat_withdrawals = models.BooleanField(default=False,
                                                              verbose_name="Снятие с фиатного счета без ограничений")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Настройки ранга {self.rank.rank_name}"


