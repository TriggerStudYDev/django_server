from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils.timezone import now
from .models import *


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

    :param user_from: Пользователь, с которого списываются средства.
    :param user_to: Пользователь, которому зачисляются средства (опционально).
    :param amount: Сумма транзакции.
    :param transaction_type: Тип транзакции.
    :param comment: Комментарий к платежу.
    :param commission: Комиссия в процентах.
    :param use_bonus: Флаг, использовать ли бонусный баланс.
    :return: Статус выполнения транзакции и комментарий.
    """
    try:
        with db_transaction.atomic():
            sender_balance = Balance.objects.get(profile=user_from.profile)
            receiver_balance = None
            if user_to:
                receiver_balance = Balance.objects.get(profile=user_to.profile)
            if commission == 0:
                total_deduction = amount
            else:
                commission_amount = (amount * commission) / 100
                total_deduction = amount + commission_amount
            bonus_used = Decimal("0.00")
            fiat_used = Decimal("0.00")
            dsc_message = ""

            # Пополнение фиатного счета
            if transaction_type == "deposit":
                sender_balance.fiat_balance += amount
                comment = comment or "Пополнение фиата"

            # Пополнение бонусного счета
            elif transaction_type == "bonus_add":
                sender_balance.bonus_balance += amount
                comment = comment or "Пополнение бонусов"

            # Перевод бонусов между пользователями
            elif transaction_type == "bonus_transfer":
                if sender_balance.bonus_balance < total_deduction:
                    shortfall = total_deduction - sender_balance.bonus_balance
                    dsc_message = f"Вам не хватило {shortfall}р"
                    raise ValueError("Недостаточно бонусов.")

                sender_balance.bonus_balance -= total_deduction
                receiver_balance.bonus_balance += amount
                comment = comment or "Перевод бонусов"

            # Оплата заказа (учитывая бонусы)
            elif transaction_type == "payment":
                if use_bonus:
                    max_bonus_usage = min(sender_balance.bonus_balance, amount)
                    sender_balance.bonus_balance -= max_bonus_usage
                    bonus_used = max_bonus_usage
                    amount -= max_bonus_usage

                if sender_balance.fiat_balance < amount + commission_amount:
                    shortfall = (amount + commission_amount) - sender_balance.fiat_balance
                    dsc_message = f"Вам не хватило {shortfall}р"
                    raise ValueError("Недостаточно фиатных средств.")

                sender_balance.fiat_balance -= (amount + commission_amount)
                fiat_used = amount + commission_amount

                if bonus_used > 0:
                    dsc_message = f"С бонусного счета было списано {bonus_used}р, с фиатного счета {fiat_used}р"

                receiver_balance.frozen_balance += amount
                comment = comment or "Оплата заказа"

            # Возврат средств
            elif transaction_type == "refund":
                sender_balance.fiat_balance += amount
                comment = comment or "Возврат средств"

            # Вывод средств (выводим средства из замороженного баланса)
            elif transaction_type == "withdrawal":
                if sender_balance.frozen_balance < total_deduction:
                    shortfall = total_deduction - sender_balance.frozen_balance
                    dsc_message = f"Вам не хватило {shortfall}р"
                    raise ValueError("Недостаточно средств для вывода.")

                sender_balance.frozen_balance -= total_deduction
                comment = comment or "Вывод средств"

            # Заморозка средств
            elif transaction_type == "freeze":
                if sender_balance.fiat_balance < amount:
                    shortfall = amount - sender_balance.fiat_balance
                    dsc_message = f"Вам не хватило {shortfall}р"
                    raise ValueError("Недостаточно средств для заморозки.")

                sender_balance.fiat_balance -= amount
                sender_balance.frozen_balance += amount
                comment = comment or "Заморозка средств"

            # Разморозка средств
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
            transaction = Transaction.objects.create(
                profile=user_from.profile,
                amount=amount,
                transaction_type=transaction_type,
                comment=comment,
                status="completed",
                dsc=dsc_message if dsc_message else None,
                created_at=now(),
                error_message="Тех. ошибки не обнаружено"
            )

            return {"status": "success", "comment": comment, "dsc": dsc_message, "transaction": transaction}

    except ValueError as e:
        error_message = str(e)
        transaction = Transaction.objects.create(
            profile=user_from.profile,
            amount=amount,
            transaction_type=transaction_type,
            comment="Ошибка платежа",
            status="failed",
            dsc=dsc_message if dsc_message else None,
            created_at=now(),
            error_message="Тех. ошибки не обнаружено" if "Недостаточно" in error_message else error_message
        )
        return {"status": "failed", "comment": "Ошибка платежа", "dsc": dsc_message, "error": error_message,
                "transaction": transaction}
