from datetime import timedelta
from decimal import Decimal
from functools import partial

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import WithdrawalRequest, Balance
from server.decorators import *
from rest_framework import generics, viewsets

from .serializers import *
from .services import process_transaction



class CreateWithdrawalRequest(APIView):
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)]

    def post(self, request):
        user = request.user
        try:
            amount = Decimal(request.data.get('amount'))  # Приводим к Decimal
        except (ValueError, TypeError):
            return Response({
                "error": "Некорректное значение суммы. Введите корректное число."
            }, status=status.HTTP_400_BAD_REQUEST)

        card_number = request.data.get('card_number')
        if not card_number:
            return Response({
                "error": "Некорректное значение номера карты. Введите поле card_number."
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = request.data.get('comment', '')

        # Минимальная сумма вывода
        if amount < Decimal('5000'):
            return Response({
                "error": f"Минимальная сумма для вывода 5000р, для успешного вывода вам не хватает {5000 - amount}р"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем дату последнего успешного вывода
        last_withdrawal = WithdrawalRequest.objects.filter(
            user=user, status="completed"
        ).order_by('-date_submitted').first()

        if last_withdrawal:
            days_since_last_withdrawal = (timezone.now().date() - last_withdrawal.date_submitted.date()).days
            remaining_days = max(7 - days_since_last_withdrawal, 0)  # Минимум 0 дней, чтобы избежать отрицательных значений

            # Если за последние 7 дней уже было 3 успешных вывода — запретить новый вывод
            week_ago = timezone.now() - timedelta(days=7)
            withdrawal_count = WithdrawalRequest.objects.filter(
                user=user, status="completed", date_submitted__gte=week_ago
            ).count()

            if withdrawal_count >= 3:
                return Response({
                    'remaining_days': remaining_days,
                    "error": f"Вы превысили количество выводов на этой неделе, вывести денежные средства вы сможете через {remaining_days} дней"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Проводим транзакцию: переводим средства с фиатного баланса на замороженный
        try:
            transaction_result = process_transaction(
                user_from=user,
                amount=amount,
                transaction_type="freeze",
                comment="На рассмотрении на вывод"
            )

            # Проверяем результат транзакции
            if transaction_result['status'] == 'failed':
                withdrawal_request = WithdrawalRequest.objects.create(
                    user=user,
                    amount=amount,
                    card_number=card_number,
                    status="cancelled_whores",
                    transaction=transaction_result['transaction'],
                    comment=comment
                )
                withdrawal_request.comment_whores = f"comment: {transaction_result['comment']}. {transaction_result['dsc']}"
                withdrawal_request.save()

                return Response({
                    "status": "failed",
                    "message": f"Заявка не была создана, ошибка при обработке вывода: {transaction_result['comment']}. {transaction_result['dsc']}"
                }, status=status.HTTP_400_BAD_REQUEST)

            else:
                withdrawal_request = WithdrawalRequest.objects.create(
                    user=user,
                    amount=amount,
                    card_number=card_number,
                    status="pending",
                    transaction=transaction_result['transaction'],
                    comment=comment
                )

                return Response({
                    "status": "success",
                    "message": "Заявка на вывод успешно создана и находится на рассмотрении",
                    "request_id": withdrawal_request.id
                }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserWithdrawalRequests(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)]
    serializer_class = WithdrawalRequestSerializer

    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get('status', None)
        queryset = WithdrawalRequest.objects.filter(user=user)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class FinanceWithdrawalRequests(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=["finance"]),
                          ]
    serializer_class = WithdrawalRequestSerializer

    def get_queryset(self):
        queryset = WithdrawalRequest.objects.all()

        # Фильтрация по параметрам из запроса
        user_filter = self.request.query_params.get('user', None)
        min_amount = self.request.query_params.get('min_amount', None)
        max_amount = self.request.query_params.get('max_amount', None)
        status_filter = self.request.query_params.get('status', None)

        if user_filter:
            queryset = queryset.filter(user__username=user_filter)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)
        if status_filter:
            queryset = queryset.filter(status__in=status_filter.split(','))

        return queryset



class ApproveRejectWithdrawalRequest(APIView):
    permission_classes = [IsAuthenticated, partial(IsRole, allowed_roles=["finance"])]

    def post(self, request, pk):
        action = request.data.get("action")  # 'approve' или 'reject'
        comment = request.data.get("comment", "").strip()

        # Получаем заявку или возвращаем 404
        withdrawal_request = get_object_or_404(WithdrawalRequest, id=pk)

        # Запрещаем изменять заявки со статусами completed, cancelled, cancelled_whores
        if withdrawal_request.status in ["completed", "cancelled", "cancelled_whores"]:
            return Response(
                {"error": "Изменение заявки запрещено, так как она уже обработана"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "approve":
            try:
                # Создаём новую транзакцию для вывода средств
                transaction = Transaction.objects.create(
                    profile=withdrawal_request.user.profile,
                    amount=withdrawal_request.amount,
                    transaction_type="withdrawal",
                    status="pending",
                    comment="Вывод средств на БК"
                )

                # Проводим транзакцию через процессинг
                transaction_result = process_transaction(
                    user_from=withdrawal_request.user,
                    amount=withdrawal_request.amount,
                    transaction_type="withdrawal",
                    comment="Вывод средств на БК",
                )

                # Если транзакция успешна, обновляем её статус
                transaction.status = "completed"
                transaction.dsc = transaction_result.get('dsc', '')
                transaction.save()

                # Обновляем заявку
                withdrawal_request.status = "completed"
                withdrawal_request.transaction = transaction  # Привязываем транзакцию к заявке
                withdrawal_request.comment_whores = f"comment: {transaction.dsc}"
                withdrawal_request.save()

                return Response(
                    {"status": "success", "message": "Заявка одобрена и обработана"}
                )

            except ValueError as e:
                # Ошибка при первой попытке - переводим в cancelled_whores и возвращаем средства
                transaction.status = "failed"
                transaction.error_message = str(e)
                transaction.save()

                withdrawal_request.status = "cancelled_whores"
                withdrawal_request.transaction = transaction  # Привязываем неудачную транзакцию
                withdrawal_request.comment_whores = f"comment: {str(e)}"
                withdrawal_request.save()

                process_transaction(
                    user_from=withdrawal_request.user,
                    amount=withdrawal_request.amount,
                    transaction_type="unfreeze",
                    comment="Возврат средств с замороженного счета на фиатный",
                )

                return Response(
                    {
                        "status": "failed",
                        "message": "Ошибка при обработке вывода, средства возвращены на фиатный счет",
                    }
                )

        elif action == "reject":
            # Проверяем, введён ли комментарий
            if not comment:
                return Response(
                    {"error": "При отклонении заявки поле комментарий является обязательным"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Создаём транзакцию на разморозку средств
            transaction = Transaction.objects.create(
                profile=withdrawal_request.user.profile,
                amount=withdrawal_request.amount,
                transaction_type="unfreeze",
                status="pending",
                comment="Возврат средств после отклонения заявки"
            )

            # Отклоняем заявку
            withdrawal_request.status = "cancelled"
            withdrawal_request.transaction = transaction  # Привязываем транзакцию к заявке
            withdrawal_request.comment_whores = comment
            withdrawal_request.save()

            # Проводим транзакцию на возврат средств
            process_transaction(
                user_from=withdrawal_request.user,
                amount=withdrawal_request.amount,
                transaction_type="unfreeze",
                comment="Возврат средств с замороженного счета на фиатный после отклонения заявки",
            )

            transaction.status = "completed"
            transaction.save()

            return Response(
                {"status": "success", "message": "Заявка отклонена, средства возвращены на фиатный счет"}
            )

        else:
            return Response(
                {"error": "Некорректное действие"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BonusTransferView(APIView):
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)
                          ]
    def post(self, request, *args, **kwargs):
        # Сериализуем входящие данные
        serializer = BonusTransferSerializer(data=request.data)

        if serializer.is_valid():
            user_from = request.user  # Текущий пользователь
            user_to = serializer.validated_data['recipient_profile'].user  # Профиль получателя
            amount = serializer.validated_data['amount']
            comment = serializer.validated_data.get('comment', '')
            # Проверка на отрицательные значения
            if amount <= 0:
                return Response({"error": "Сумма должна быть положительной."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Проверяем, не отправляет ли пользователь перевод самому себе
            if user_from == user_to:
                return Response(
                    {"error": "Перевод бонусов себе невозможен"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Вызываем функцию обработки транзакции
            result = process_transaction(
                user_from=user_from,
                user_to=user_to,  # Передаем пользователя (не профиль) в функцию
                amount=amount,
                transaction_type="bonus_transfer",
                comment=comment
            )

            if result['status'] == 'success':
                return Response({
                    "status": "success",
                    "transaction": result["status"],
                    "comment": result["comment"],
                    "dsc": result["dsc"]
                }, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Balance.objects.all()  # Все балансы пользователей
    serializer_class = BalanceSerializer
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)
                          ]

    def get_queryset(self):
        # Получаем баланс только для текущего пользователя
        return Balance.objects.filter(profile__user=self.request.user)