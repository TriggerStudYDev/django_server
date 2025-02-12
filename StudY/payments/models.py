from django.db import models
from server.models import *


class Balance(models.Model):
    """Баланс пользователя"""
    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Баланс пользователей'

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, verbose_name='Профиль')
    fiat_balance = models.DecimalField(verbose_name='Фиатный счет', max_digits=10, decimal_places=2, default=0)
    frozen_balance = models.DecimalField(verbose_name='Замороженный счет', max_digits=10, decimal_places=2, default=0)
    bonus_balance = models.DecimalField(verbose_name='Бонусный счет', max_digits=10, decimal_places=2, default=0)
    forfeited_balance = models.DecimalField(verbose_name='Баланс упущенной прибыли', max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Баланс {self.profile.user.username}'


class WithdrawalRequest(models.Model):
    """Заявка на вывод средств"""
    class Meta:
        verbose_name = 'Заявка на вывод'
        verbose_name_plural = 'Заявки на вывод'

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    amount = models.DecimalField(verbose_name='Сумма', max_digits=10, decimal_places=2)
    card_number = models.CharField(verbose_name='Номер кредитной карты', max_length=255, null=True, blank=True)
    status = models.CharField(
        verbose_name='Статус заявки', max_length=40, choices=[
            ('pending', 'В обработке'),
            ('completed', 'Завершена'),
            ('cancelled', 'Отклонена'),
            ('cancelled_whores', 'Отклонена платежным шлюзом')
        ], default='pending'
    )
    transaction = models.OneToOneField("Transaction", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанная транзакция")
    date_submitted = models.DateTimeField(verbose_name='Дата подачи', auto_now_add=True)
    date_updated = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)
    date_completed = models.DateTimeField(verbose_name='Дата завершения', null=True, blank=True)
    comment = models.CharField(verbose_name='Комментарий', max_length=255, null=True, blank=True)
    comment_user = models.CharField(verbose_name='Комментарий пользователя', max_length=255, null=True, blank=True)
    comment_whores = models.CharField(verbose_name='Комментарий шлюза', max_length=255, null=True, blank=True)


    def __str__(self):
        return f'Вывод {self.user.username} | {self.amount} ({self.get_status_display()})'


class Transaction(models.Model):
    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-created_at']

    TRANSACTION_TYPES = [
        ('bonus_add', 'Пополнение бонусов'),
        ('bonus_transfer', 'Перевод бонусов'),
        ('deposit', 'Пополнение фиата'),
        ('withdrawal', 'Вывод фиата'),
        ('payment', 'Оплата заказа фиатом'),
        ('payment_bonus', 'Оплата внутренней покупки бонусами'),
        ('payment_mixed', 'Оплата заказа/покупки бонусами + фиатом'),
        ('refund', 'Возврат средств'),
        ('freeze', 'Заморозка средств'),
        ('unfreeze', 'Разморозка средств'),
        ('penalty', 'Штраф (списание средств)'),
        ('compensation', 'Компенсация (начисление средств)'),
        ('fiat_transfer', 'Перевод фиата между пользователями'),
    ]

    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('completed', 'Завершено'),
        ('cancel', 'Отклонено'),
        ('failed', 'Ошибка'),
        ('frozen', 'Заморожено'),
        ('waiting_confirmation', 'Ожидание подтверждения'),
        ('reversed', 'Отменено после обработки'),
        ('penalized', 'Санкционное списание'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="transactions", verbose_name="Профиль отправителя")
    target_profile = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_transactions", verbose_name="Профиль получателя"
    )
    amount = models.DecimalField(verbose_name="Сумма", max_digits=10, decimal_places=2)
    transaction_type = models.CharField(verbose_name="Тип", max_length=155, choices=TRANSACTION_TYPES)
    comment = models.CharField(verbose_name='Комментарий', max_length=155, blank=True, null=True)
    status = models.CharField(verbose_name="Статус", max_length=155, choices=STATUS_CHOICES, default='completed')
    error_message = models.TextField(verbose_name="Ошибка", blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    dsc = models.CharField(verbose_name='Дополнение', max_length=155, null=True, blank=True)


    def __str__(self):
        return f"{self.profile.user.username} | {self.transaction_type} | {self.amount} | {self.get_status_display()}"
