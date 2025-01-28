from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class ExampleModel(models.Model):
    name = models.CharField(verbose_name='Имя', max_length=100)
    dsc = models.TextField(verbose_name='Описание')


class TestViews(models.Model):
    class Meta:
        verbose_name = 'Тестовая таблица'
        verbose_name_plural = 'Тестовые таблицы'

    SELECT = [
        ('voice1', 'Выбор 1'),
        ('voice2', 'Выбор 2'),
        ('voice3', 'Выбор 3'),
    ]

    voice = models.CharField(verbose_name='Выбор 1', max_length=10, choices=SELECT)
    dsc = models.TextField(verbose_name='Описание')
    date_start = models.DateField(verbose_name='Дата создания', auto_created=True)
    data_end = models.DateTimeField(verbose_name='Дата завершения')
    is_active = models.BooleanField(verbose_name='Активный', default=True)


# Актуальные таблицы


class User(AbstractUser):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    ROLE_CHOICES = [
        ('заказчик', 'Заказчик'),
        ('исполнитель', 'Исполнитель'),
        ('проверяющий', 'Проверяющий'),
        ('администратор', 'Администратор'),
    ]

    first_name = models.CharField(verbose_name='Имя', max_length=100, default='Админ')
    last_name = models.CharField(verbose_name='Фамилия', max_length=100, default='Админ')
    middle_name = models.CharField(verbose_name='Отчество', max_length=100, blank=True, null=True)

    role = models.CharField(verbose_name='Роль пользователя', max_length=20, choices=ROLE_CHOICES, default='администратор')
    is_active = models.BooleanField(verbose_name='Активен', default=True)
    last_activity = models.DateTimeField(verbose_name='Дата последней активности', auto_now=True)
    is_verification = models.BooleanField(verbose_name='Верификация', default=False)

    @property
    def has_balance(self):
        return self.role in ['заказчик', 'исполнитель']

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
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, verbose_name='Университет')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, verbose_name='Факультет')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name='Кафедра')
    disciplines = models.ManyToManyField(Discipline, verbose_name='Дисциплины', null=True, blank=True)
    form_of_study = models.ForeignKey(FormOfStudy, on_delete=models.SET_NULL, null=True, verbose_name='Форма обучения')
    vk_profile = models.CharField(verbose_name='Ссылка на ВКонтакте', max_length=100, blank=True, null=True,
                                  unique=True)
    telegram_username = models.CharField(verbose_name='Телеграмм', max_length=100, blank=True, null=True, unique=True)


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


class Balance(models.Model):
    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Баланс пользователей'

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    fiat_balance = models.DecimalField(verbose_name='Фиатный баланс', max_digits=10, decimal_places=2, default=0)
    frozen_balance = models.DecimalField(verbose_name='Замороженный баланс', max_digits=10, decimal_places=2, default=0)
    forfeited_balance = models.DecimalField(verbose_name='Баланс упущенной прибыли', max_digits=10, decimal_places=2,
                                            default=0)

    def __str__(self):
        return f'Баланс пользователя {self.user.username}'


class WithdrawalRequest(models.Model):
    class Meta:
        verbose_name = 'Заявка на вывод средств'
        verbose_name_plural = 'Заявки на вывод средств'

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    amount = models.DecimalField(verbose_name='Сумма', max_digits=10, decimal_places=2)
    card_number = models.CharField(verbose_name='Номер карты', max_length=255)
    status = models.CharField(
        verbose_name='Статус заявки', max_length=40, choices=[
            ('В обработке', 'В обработке'),
            ('Завершена', 'Завершена'),
            ('Отклонена', 'Отклонена')
        ], default='В обработке'
    )
    date_submitted = models.DateTimeField(verbose_name='Дата подачи заявки', auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)
    date_completed = models.DateTimeField(verbose_name='Дата завершения', null=True, blank=True)
    comment = models.CharField(verbose_name='Комментарий', max_length=255, null=True, blank=True)

    def __str__(self):
        return f'Заявка на вывод средств пользователя {self.user.username}'


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