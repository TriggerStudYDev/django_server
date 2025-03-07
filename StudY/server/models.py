from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import secrets
import string
from rank.models import *


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
    count_auth = models.IntegerField(verbose_name='Кол-во авторизаций', default=0)

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
    rank = models.ForeignKey(Rank, verbose_name='Ранг', on_delete=models.PROTECT)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, verbose_name='Университет')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, verbose_name='Факультет')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name='Кафедра')
    disciplines = models.ManyToManyField(Discipline, verbose_name='Дисциплины', null=True, blank=True)
    course = models.IntegerField(verbose_name='Курс обучения', default=1)
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
        ('Повторная проверка', 'Повторная проверка'),
        ('Отклонена верификация по СБ', 'Отклонена верификация по СБ'),
        ('Отклонена анкета исполнителя', 'Отклонена анкета исполнителя'),
        ('Отправлен на доработку', 'Отправлен на доработку'),
        ('Принят', 'Принят')

    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, verbose_name='Профиль')
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



