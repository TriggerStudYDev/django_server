from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils.timezone import now
from requests import Response
from rest_framework import status
import logging
from .models import *
from rank.services import check_user_rank

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
        is_profile=False,
        rank_commission=0

):
    """
    Функция обработки платежей в системе.
    """
    try:
        with db_transaction.atomic():
            # Получаем балансы пользователей
            if is_profile:
                sender_balance = Balance.objects.get(profile=user_from)
            else:
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
                if is_profile:
                    receiver_limit = check_user_rank(user_from, "bonus_account_limit", is_profile=True)
                else:
                    receiver_limit = check_user_rank(user_from.profile, "bonus_account_limit")
                if receiver_limit is False:
                    raise ValueError("Ошибка получения лимита бонусного счета")
                current_receiver_bonus = sender_balance.bonus_balance
                available_limit = receiver_limit - current_receiver_bonus

                if available_limit >= amount:
                    # Полное зачисление бонусов
                    sender_balance.bonus_balance += amount + (amount * rank_commission / 100)
                    comment = comment or "Пополнение бонусов"
                    if is_profile:
                        transaction = create_transaction(
                            user_from, amount+ (amount * rank_commission / 100), "bonus_add", comment, "completed"
                        )
                    else:
                        transaction = create_transaction(
                            user_from.profile, amount, "bonus_add", comment, "completed"
                        )
                    sender_balance.save()

                    return {
                        "status": "success",
                        "comment": f"Пополнение бонусного счета на {amount}р выполнено",
                        "dsc": f"Ваш бонусный баланс пополнен на {amount}р",
                        "transaction": transaction_to_dict(transaction)
                    }

                elif available_limit > 0:
                    if is_profile:
                        user = user_from
                    else:
                        user = user_from.profile
                    # Частичное зачисление + остаток в упущенную прибыль
                    sender_balance.bonus_balance += available_limit
                    forfeited_amount = amount - available_limit
                    sender_balance.forfeited_balance += forfeited_amount
                    transaction_success = create_transaction(
                        user, available_limit, "bonus_add",
                        f"Частичное пополнение бонусов ({available_limit}р)", "completed"
                    )
                    transaction_forfeited = create_transaction(
                        user, forfeited_amount, "bonus_forfeited",
                        f"Вам предназначалось {amount}р, к сожалению ваш лимит на бонусный счет заполнен, "
                        f"остаток {forfeited_amount}р не смогли перевести  .", "completed"
                    )
                    sender_balance.save()
                    return {
                        "status": "partial_success",
                        "comment": f"Пополнение {available_limit}р, остаток {forfeited_amount}р не переведен",
                        "dsc": f"Вам предназначалось {amount}р, но ваш лимит заполнен, остаток {forfeited_amount}р зачислен "
                               f"в упущенную прибыль.",
                        "transactions": [
                            transaction_to_dict(transaction_success),
                            transaction_to_dict(transaction_forfeited)
                        ]
                    }
                else:
                    # Лимит уже заполнен, весь бонус уходит в упущенную прибыль
                    sender_balance.forfeited_balance += amount
                    transaction_forfeited = create_transaction(
                        user_from.profile, amount, "bonus_forfeited",
                        f"Вам предназначалось {amount}р, к сожалению ваш лимит на бонусный счет заполнен, "
                        f"перевод не выполнен.", "completed"

                    )
                    sender_balance.save()
                    return {
                        "status": "failed",
                        "comment": f"Пополнение не выполнено: ваш лимит заполнен, сумма {amount}р зачислена в упущенную прибыль.",
                        "dsc": f"Вам предназначалось {amount}р, но ваш лимит заполнен, сумма зачислена в упущенную прибыль.",
                        "transactions": [transaction_to_dict(transaction_forfeited)]
                    }

            elif transaction_type == "bonus_transfer":
                if sender_balance.bonus_balance < total_deduction:
                    shortfall = total_deduction - sender_balance.bonus_balance
                    raise ValueError(f"Недостаточно бонусов. Вам не хватает {shortfall}р")

                # Проверяем лимит бонусного счета у получателя

                receiver_limit = check_user_rank(user_to, "bonus_account_limit")
                if receiver_limit is False:
                    raise ValueError("Ошибка получения лимита бонусного счета")

                current_receiver_bonus = receiver_balance.bonus_balance
                available_limit = receiver_limit - current_receiver_bonus
                if available_limit >= amount:
                    # Полный перевод возможен
                    sender_balance.bonus_balance -= total_deduction
                    receiver_balance.bonus_balance += amount
                    dsc_message = f"Перевод бонусов {amount}р"
                    transaction_out = create_transaction(
                        user_from.profile, amount, "bonus_transfer", f"Перевод бонусов пользователю {user_to.username}"
                    )
                    transaction_in = create_transaction(
                        user_to.profile, amount, "bonus_add", f"Пополнение бонусов от {user_from.username}"
                    )
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

                elif available_limit > 0:
                    # Частичный перевод (переводим только доступную сумму)
                    sender_balance.bonus_balance -= available_limit
                    receiver_balance.bonus_balance += available_limit
                    transaction_out_partial = create_transaction(
                        user_from.profile, available_limit, "bonus_transfer",
                        f"Частичный перевод бонусов пользователю {user_to.username}"
                    )

                    transaction_in_partial = create_transaction(
                        user_to.profile, available_limit, "bonus_add",
                        f"Пополнение бонусов от {user_from.username}"
                    )
                    # Неуспешная транзакция на оставшуюся сумму
                    failed_amount = amount - available_limit
                    transaction_out_failed = create_transaction(
                        user_from.profile, failed_amount, "bonus_transfer_failed",
                        "У {} заполнился лимит, перевод невозможен".format(user_to.username),
                        "failed"
                    )
                    sender_balance.save()
                    receiver_balance.save()
                    return {
                        "status": "partial_success",
                        "comment": f"Частичный перевод {available_limit}р, оставшиеся {failed_amount}р не переведены",
                        "dsc": f"Вам хотели перевести {amount}р, к сожалению ваш лимит заполнился",
                        "transactions": [
                            transaction_to_dict(transaction_out_partial),
                            transaction_to_dict(transaction_in_partial),
                            transaction_to_dict(transaction_out_failed)
                        ]
                    }

                else:
                    # Лимит получателя уже заполнен — перевод невозможен
                    transaction_out_failed = create_transaction(
                        user_from.profile, amount, "bonus_transfer_failed",
                        "У {} заполнился лимит, перевод невозможен".format(user_to.username),
                        "failed"
                    )

                    return {
                        "status": "failed",
                        "comment": f"Перевод невозможен: у {user_to.username} достигнут лимит",
                        "dsc": f"Вам хотели перевести {amount}р, но ваш лимит уже заполнен",
                        "transactions": [transaction_to_dict(transaction_out_failed)]
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

