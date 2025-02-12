from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import secrets
import string


class User(AbstractUser):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    ROLE_CHOICES = [
        ('заказчик', 'Заказчик'),
        ('исполнитель', 'Исполнитель'),
        ('проверяющий', 'Проверяющий'),
        ('администратор', 'Администратор'),
        ("finance", 'Финансист')
    ]

    first_name = models.CharField(verbose_name='Имя', max_length=100, default='Админ')
    last_name = models.CharField(verbose_name='Фамилия', max_length=100, default='Админ')
    middle_name = models.CharField(verbose_name='Отчество', max_length=100, blank=True, null=True)

    role = models.CharField(verbose_name='Роль пользователя', max_length=20, choices=ROLE_CHOICES,
                            default='администратор')
    is_active = models.BooleanField(verbose_name='Активен', default=True)
    last_activity = models.DateTimeField(verbose_name='Дата последней активности', auto_now=True)
    is_verification = models.BooleanField(verbose_name='Верификация', default=False)
    referral_code = models.CharField(
        max_length=20, unique=True, null=True, blank=True, verbose_name="Реферальный код"
    )

    @property
    def has_balance(self):
        return self.role in ['заказчик', 'исполнитель']

    def generate_referral_code(self):
        if self.role in ['заказчик', 'исполнитель']:
            # Генерация кода из 8 символов (буквы + цифры)
            alphabet = string.ascii_uppercase + string.digits
            code = ''.join(secrets.choice(alphabet) for _ in range(20))

            # Проверка уникальности
            while User.objects.filter(referral_code=code).exists():
                code = ''.join(secrets.choice(alphabet) for _ in range(20))
            return code
        return None

    def save(self, *args, **kwargs):
        if not self.referral_code:  # Генерируем код только при создании
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.role})'


class University(models.Model):
    class Meta:
        verbose_name = 'Университет'
        verbose_name_plural = 'Университеты'

    name = models.CharField(verbose_name='Наименование университета', max_length=255)
    photo = models.ImageField(verbose_name='Фотография', upload_to='university/photo/%Y/%m/%d/', null=True,
                              blank=True)

    def __str__(self):
        return self.name


class Faculty(models.Model):
    class Meta:
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'

    university = models.ForeignKey(University, on_delete=models.CASCADE, verbose_name='Университет')
    name = models.CharField(verbose_name='Наименование факультета', max_length=255)
    photo = models.ImageField(verbose_name='Фотография', upload_to='faculty/photo/%Y/%m/%d/', null=True,
                              blank=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    class Meta:
        verbose_name = 'Кафедра'
        verbose_name_plural = 'Кафедры'

    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, verbose_name='Факультет')
    name = models.CharField(verbose_name='Наименование кафедры', max_length=255)
    photo = models.ImageField(verbose_name='Фотография', upload_to='department/photo/%Y/%m/%d/', null=True,
                              blank=True)

    def __str__(self):
        return self.name


class Discipline(models.Model):
    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'

    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Кафедра')
    name = models.CharField(verbose_name='Наименование дисциплины', max_length=255)
    photo = models.ImageField(verbose_name='Фотография', upload_to='discipline/photo/%Y/%m/%d/', null=True,
                              blank=True)

    def __str__(self):
        return self.name


class FormOfStudy(models.Model):
    class Meta:
        verbose_name = 'Форма обучения'
        verbose_name_plural = 'Формы обучения'

    name = models.CharField(verbose_name='Наименование формы обучения', max_length=255)

    def __str__(self):
        return self.name


class Profile(models.Model):
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    photo = models.ImageField(verbose_name='Фотография', upload_to='user_profile_photo/%Y/%m/%d/', null=True,
                              blank=True)
    rank = models.ForeignKey('Rank', verbose_name='Ранг', on_delete=models.PROTECT)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, verbose_name='Университет')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, verbose_name='Факультет')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name='Кафедра')
    disciplines = models.ManyToManyField(Discipline, verbose_name='Дисциплины', null=True, blank=True)
    form_of_study = models.ForeignKey(FormOfStudy, on_delete=models.SET_NULL, null=True, verbose_name='Форма обучения')
    vk_profile = models.CharField(verbose_name='Ссылка на ВКонтакте', max_length=100, blank=True, null=True,
                                  unique=True)
    telegram_username = models.CharField(verbose_name='Телеграмм', max_length=100, blank=True, null=True, unique=True)


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


class StudentCard(models.Model):
    class Meta:
        verbose_name = 'Верификация аккаунта'
        verbose_name_plural = 'Верификация аккаунтов'

    STATUS_CHOICES = [
        ('На проверке', 'На проверке'),
        ('Отклонена верификация по СБ', 'Отклонена верификация по СБ'),
        ('Отклонена анкета исполнителя', 'Отклонена анкета исполнителя'),
        ('Отправлен на доработку', 'Отправлен на доработку'),
        ('Принят', 'Принят')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, verbose_name='Пользователь')
    student_card_number = models.CharField(verbose_name='Номер студенческого билета', max_length=100, null=True)
    photo = models.ImageField(verbose_name='Фотография студенческого билета', upload_to='student_cards/%Y/%m/%d/')
    about_self = models.TextField(verbose_name='О себе', null=True, blank=True)

    status = models.CharField(
        verbose_name='Статус верификации', max_length=60, choices=STATUS_CHOICES, default='На проверке'
    )

    def __str__(self):
        return f'Студенческий билет пользователя {self.user.username}'


class CustomerFeedback(models.Model):
    class Meta:
        verbose_name = 'Обратная связь от заказчика (верификация)'
        verbose_name_plural = 'Обратные связи от заказчика (верификация)'

    student_card = models.ForeignKey(StudentCard, verbose_name='Заявка на верификацию', on_delete=models.PROTECT)
    photo = models.FileField(verbose_name='Файл',
                             upload_to='student_cards/customer_feedback/%Y/%m/%d/')


class Portfolio(models.Model):
    class Meta:
        verbose_name = 'Портфолио исполнителя (верификация)'
        verbose_name_plural = 'Портфолио исполнителей (верификация)'

    student_card = models.ForeignKey(StudentCard, verbose_name='Заявка на верификацию', on_delete=models.PROTECT)
    photo = models.FileField(verbose_name='Файл',
                             upload_to='student_cards/portfolio/%Y/%m/%d/')


class StudentCardComment(models.Model):
    class Meta:
        verbose_name = 'Комментарий к верификации аккаунта'
        verbose_name_plural = 'Комментарии к верификации аккаунтов'

    student_card = models.ForeignKey(StudentCard, on_delete=models.CASCADE, related_name='comments',
                                     verbose_name='Студенческий билет')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор комментария')

    def __str__(self):
        return f'Комментарий для студенческого билета {self.student_card.student_card_number}'


class ReferralSettings(models.Model):
    class Meta:
        verbose_name = "Настройка реферальной программы"
        verbose_name_plural = "Настройки реферальных программ"

    role = models.CharField(
        max_length=20,
        choices=[('customer', 'Заказчик'), ('executor', 'Исполнитель')],
        verbose_name="Роль"
    )
    level = models.PositiveIntegerField(verbose_name="Уровень")
    bonus_ref_user = models.DecimalField(max_digits=5,
                                         decimal_places=2,
                                         verbose_name="Зачисление реф бонусов", null=True, blank=True)
    bonus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Зачисление бонусов"
    )
    required_orders = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Требуемое количество заказов (для заказчиков)"
    )
    required_earnings = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Требуемый заработок (для исполнителей)"
    )

    min_order_value = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Минимальная сумма заказа (для заказчиков)"
    )
    min_earning = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Минимальный заработок (для исполнителей)"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")

    class Meta:
        verbose_name = "Настройка реферальной программы"
        verbose_name_plural = "Настройки реферальных программ"

    def __str__(self):
        return f"{self.role} Уровень {self.level}"


class Referral(models.Model):
    referrer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referrals", verbose_name="Пригласивший"
    )
    referred = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="referral", verbose_name="Приглашенный"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации реферала")

    class Meta:
        verbose_name = "Реферальная связь"
        verbose_name_plural = "Реферальные связи"

    def __str__(self):
        return f"{self.referrer.username} → {self.referred.username}"


class ReferralActivity(models.Model):
    class Meta:
        verbose_name = "Активность реферала"
        verbose_name_plural = "Активности рефералов"
        unique_together = ('user', 'referral')

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referral_activities", verbose_name="Пользователь"
    )
    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="activities", verbose_name="Реферальная связь"
    )

    completed_orders = models.PositiveIntegerField(default=0, verbose_name="Завершённые заказы")
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общий заработок")
    is_bonus_available = models.BooleanField(default=False, verbose_name="Бонус доступен для вывода")
    bonus_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Полученные бонусы")
    is_bonus_claimed = models.BooleanField(default=False, verbose_name="Бонус за уровень получен")

    activity_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата активности")

    def __str__(self):
        return f"Активность {self.user.username}"

    def get_current_level(self):
        role = self.user.role  # Предполагаем, что у user есть поле role (customer/executor)
        if role == "customer":
            settings = ReferralSettings.objects.filter(role=role, required_orders__lte=self.completed_orders)
        else:
            settings = ReferralSettings.objects.filter(role=role, required_earnings__lte=self.total_earnings)
        if settings.exists():
            return settings.order_by('-level').first().level  # Берем максимальный уровень
        return 1  # По умолчанию 1-й уровень


class ReferralBonus(models.Model):
    class Meta:
        verbose_name = "Реферальный бонус"
        verbose_name_plural = "Реферальные бонусы"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="referral_bonuses", verbose_name="Пользователь"
    )
    referral_activity = models.ForeignKey(
        ReferralActivity, on_delete=models.CASCADE, related_name="bonuses", verbose_name="Активность реферала"
    )
    referral_settings = models.ForeignKey(
        ReferralSettings, on_delete=models.CASCADE, related_name="bonuses", verbose_name="Настройки уровня"
    )

    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Сумма бонуса"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата начисления")

    def __str__(self):
        return f"Бонус {self.user.username} - {self.amount}"


class Order(models.Model):
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    STATUS_CHOICES = [
        ('в разработке', 'В разработке'),
        ('на согласовании', 'На согласовании'),
        ('отправлен на доработку', 'Отправлен на доработку'),
        ('завершен', 'Завершен'),
        ('отклонен', 'Отклонен'),
    ]

    TYPE_CHOICES = [
        ('Лекция', 'Лекция'),
        ('Практика', 'Практика'),
        ('Лабораторная', 'Лабораторная'),
        ('Курсовой', 'Курсовой'),
        ('Диплом', 'Диплом'),
        ('Другое', 'Другое',)
    ]

    customer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='orders', verbose_name='Заказчик')
    performer = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='assigned_orders', verbose_name='Исполнитель')
    title = models.CharField(verbose_name='Название заказа', max_length=255)
    type_order = models.CharField(verbose_name='Тип заказа', max_length=40, choices=TYPE_CHOICES)
    description = models.TextField(verbose_name='Описание заказа')
    cost = models.DecimalField(verbose_name='Стоимость', max_digits=10, decimal_places=2)
    status = models.CharField(verbose_name='Статус заказа', max_length=30, choices=STATUS_CHOICES,
                              default='на согласовании')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    last_modified_at = models.DateTimeField(verbose_name='Дата последнего изменения', auto_now=True)
    deadlines = models.DateTimeField(verbose_name='Дедлайн')
    warranty_period_until = models.DateTimeField(verbose_name='Гарантийный период до', null=True, blank=True)

    def __str__(self):
        return f'Заказ {self.title} ({self.status})'


class OrderStatusLog(models.Model):
    class Meta:
        verbose_name = 'Лог статуса заказа'
        verbose_name_plural = 'Логи статусов заказов'

    ORDER_STATUS_CHOICES = [
        ('в разработке', 'В разработке'),
        ('на согласовании', 'На согласовании'),
        ('отправлен на доработку', 'Отправлен на доработку'),
        ('завершен', 'Завершен'),
        ('отклонен', 'Отклонен'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs', verbose_name='Заказ')
    status = models.CharField(verbose_name='Статус', max_length=50, choices=ORDER_STATUS_CHOICES)
    date_changed = models.DateTimeField(verbose_name='Дата изменения', auto_now_add=True)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)

    def __str__(self):
        return f'Лог статуса для заказа {self.order.title} ({self.status})'


class FailedLoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # IP-адрес пользователя
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Сессионный ключ
    attempts = models.IntegerField(default=0)  # Количество неудачных попыток
    last_attempt_time = models.DateTimeField(null=True, blank=True)  # Время последней неудачной попытки
    block_until = models.DateTimeField(null=True, blank=True)  # Время, до которого блокируется пользователь

    def __str__(self):
        return f"Failed login attempts for {self.user.username if self.user else self.session_key}"

    def reset_attempts(self):
        self.attempts = 0
        self.last_attempt_time = None
        self.block_until = None
        self.save()

    def increment_attempts(self):
        if self.attempts == 0 or (
                self.last_attempt_time and timezone.now() - self.last_attempt_time > timezone.timedelta(minutes=10)):
            self.attempts = 1
        else:
            self.attempts += 1
        self.last_attempt_time = timezone.now()
        self.save()

    def is_locked(self):
        if self.block_until and timezone.now() < self.block_until:
            return True
        return False

    def lock_account(self):
        self.block_until = timezone.now() + timezone.timedelta(minutes=10)
        self.save()


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

    # Уникальные привилегии (bool)
    notifications_to_executor = models.BooleanField(default=False, verbose_name="Уведомления исполнителю")
    market_price_stats = models.BooleanField(default=False, verbose_name="Вывод статистики рыночных цен")
    extra_discount_per_order = models.BooleanField(default=False, verbose_name="Дополнительная скидка после каждого заказа")
    visibility_other_universities = models.BooleanField(default=False, verbose_name="Видимость исполнителей из других университетов")
    bonus_to_fiat_transfer = models.BooleanField(default=False, verbose_name="Перевод бонусов в фиат")

    # Привилегии исполнителя (bool)
    monthly_contests = models.BooleanField(default=False, verbose_name="Участие в ежемесячных конкурсах")
    create_internal_courses = models.BooleanField(default=False, verbose_name="Доступ к созданию внутренних курсов")
    publish_articles = models.BooleanField(default=False, verbose_name="Публикация статей")
    upload_work_to_study = models.BooleanField(default=False, verbose_name="Загрузка успешных работ в справочник StudY")
    mandatory_review = models.BooleanField(default=False, verbose_name="Обязательный отзыв от заказчика")
    unlimited_fiat_withdrawals = models.BooleanField(default=False, verbose_name="Вывод фиатных средств без ограничений")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Настройки ранга {self.rank.rank_name}"

