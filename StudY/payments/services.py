from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils.timezone import now
from requests import Response
from rest_framework import status
import logging
from .models import *

logger = logging.getLogger(__name__)


def generate_transaction_description(transaction_type, amount, bonus_used=Decimal("0.00"), fiat_used=Decimal("0.00")):
    """Генерирует описание транзакции в зависимости от типа."""
    if transaction_type == "payment":
        return f"С бонусного счета было списано {bonus_used}р, с фиатного счета {fiat_used}р"
    elif transaction_type == "bonus_transfer":
        return f"Перевод бонусов на сумму {amount}р"
    return "Неизвестная транзакция"


def create_transaction(profile, amount, transaction_type, comment, status="completed", dsc=""):
    """Универсальная функция для создания транзакций."""
    return Transaction.objects.create(
        profile=profile,
        amount=amount,
        transaction_type=transaction_type,
        comment=comment,
        status=status,
        dsc=dsc,
        created_at=now(),
        error_message="Тех. ошибки не обнаружено"
    )


def process_transaction(
        user_from,
        user_to=None,
        amount: Decimal = Decimal("0.00"),
        transaction_type: str = "",
        comment: str = "",
        commission: int = 0,
        use_bonus: bool = False,

):
    """
    Функция обработки платежей в системе.
    """
    try:
        with db_transaction.atomic():
            # Получаем балансы пользователей
            sender_balance = Balance.objects.get(profile=user_from.profile)
            receiver_balance = Balance.objects.get(profile=user_to.profile) if user_to else None

            # Рассчитываем комиссию
            commission_amount = (amount * commission) / 100 if commission > 0 else Decimal("0.00")
            total_deduction = amount + commission_amount if commission > 0 else amount

            bonus_used = Decimal("0.00")
            fiat_used = Decimal("0.00")
            dsc_message = ""

            # Обрабатываем разные типы транзакций
            if transaction_type == "deposit":
                sender_balance.fiat_balance += amount
                comment = comment or "Пополнение фиата"

            elif transaction_type == "bonus_add":
                sender_balance.bonus_balance += amount
                comment = comment or "Пополнение бонусов"

            elif transaction_type == "bonus_transfer":
                if sender_balance.bonus_balance < total_deduction:
                    shortfall = total_deduction - sender_balance.bonus_balance
                    raise ValueError(f"Недостаточно бонусов. Вам не хватает {shortfall}р")

                sender_balance.bonus_balance -= total_deduction
                receiver_balance.bonus_balance += amount
                dsc_message = comment or "Перевод бонусов"

                # Создаем транзакции для перевода бонусов
                transaction_out = create_transaction(user_from.profile, amount, "bonus_transfer",
                                                     f"Перевод бонусов пользователю {user_to.username}")
                transaction_in = create_transaction(user_to.profile, amount, "bonus_add",
                                                    f"Пополнение бонусов от {user_from.username}")

                sender_balance.save()
                receiver_balance.save()

                return {
                    "status": "success",
                    "comment": f"Перевод {amount}р пользователю {user_to.username} выполнен",
                    "dsc": dsc_message,
                    "transactions": [
                        transaction_to_dict(transaction_out),
                        transaction_to_dict(transaction_in)
                    ]
                }

            elif transaction_type == "payment":
                if use_bonus:
                    max_bonus_usage = min(sender_balance.bonus_balance, amount)
                    sender_balance.bonus_balance -= max_bonus_usage
                    bonus_used = max_bonus_usage
                    amount -= max_bonus_usage

                if sender_balance.fiat_balance < amount + commission_amount:
                    shortfall = (amount + commission_amount) - sender_balance.fiat_balance
                    raise ValueError(f"Недостаточно фиатных средств. Вам не хватает {shortfall}р")

                sender_balance.fiat_balance -= (amount + commission_amount)
                fiat_used = amount + commission_amount
                dsc_message = generate_transaction_description(transaction_type, amount, bonus_used, fiat_used)

                # receiver_balance.frozen_balance += amount
                comment = comment or "Оплата с фиатного счета"

            elif transaction_type == "refund":
                sender_balance.fiat_balance += amount
                comment = comment or "Возврат средств"

            elif transaction_type == "withdrawal":
                if sender_balance.frozen_balance < total_deduction:
                    shortfall = total_deduction - sender_balance.frozen_balance
                    raise ValueError(f"Недостаточно средств для вывода. Не хватает {shortfall}р")

                sender_balance.frozen_balance -= total_deduction
                comment = comment or "Вывод средств"

            elif transaction_type == "freeze":
                if sender_balance.fiat_balance < amount:
                    shortfall = amount - sender_balance.fiat_balance
                    raise ValueError(f"Недостаточно средств для заморозки. Не хватает {shortfall}р")

                sender_balance.fiat_balance -= amount
                sender_balance.frozen_balance += amount
                comment = comment or "Заморозка средств"

            elif transaction_type == "unfreeze":
                if sender_balance.frozen_balance < amount:
                    raise ValueError("Недостаточно замороженных средств.")

                sender_balance.frozen_balance -= amount
                sender_balance.fiat_balance += amount
                comment = comment or "Разморозка средств"

            else:
                raise ValueError("Некорректный тип транзакции.")

            # Сохраняем изменения в балансах
            sender_balance.save()
            if receiver_balance:
                receiver_balance.save()

            # Записываем успешную транзакцию
            transaction = create_transaction(user_from.profile, amount, transaction_type, comment, "completed",
                                             dsc_message)

            return {
                "status": "success",
                "comment": comment,
                "dsc": dsc_message,
                "transaction": transaction  # Возвращаем сам объект модели
            }

    except ValueError as e:
        error_message = str(e)
        logger.error(f"Ошибка при обработке транзакции: {error_message}, тип: {transaction_type}")

        # В случае ошибки создаем транзакцию с неудачным статусом
        transaction = create_transaction(user_from.profile, amount, transaction_type, "Ошибка платежа", "failed",
                                         error_message)

        return {"status": "failed",
                "comment": "Ошибка платежа",
                "dsc": dsc_message,
                "error": error_message,
                "transaction": transaction_to_dict(transaction)}

def transaction_to_dict(transaction):
    """
    Преобразует объект транзакции в словарь, чтобы избежать проблемы сериализации.
    """
    return {
        "id": transaction.id,
        "profile": transaction.profile.user.username,
        "target_profile": transaction.target_profile.user.username if transaction.target_profile else None,
        "amount": str(transaction.amount),
        "transaction_type": transaction.transaction_type,
        "status": transaction.status,
        "comment": transaction.comment,
        "dsc": transaction.dsc,
        "created_at": transaction.created_at.isoformat(),
        "error_message": transaction.error_message
    }

