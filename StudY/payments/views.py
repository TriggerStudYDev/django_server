from decimal import Decimal
from functools import partial

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
        comment = request.data.get('comment', '')

        # Минимальная сумма вывода
        if amount < Decimal('5000'):
            return Response({
                "error": f"Минимальная сумма для вывода 5000р, для успешного вывода вам не хватает {5000 - amount}р"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на количество выводов за неделю
        week_start = timezone.now() - timezone.timedelta(weeks=1)
        withdrawal_count = WithdrawalRequest.objects.filter(
            user=user, status="completed", date_submitted__gte=week_start).count()

        if withdrawal_count >= 3:
            remaining_days = 7 - (timezone.now() - week_start).days
            return Response({
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
                # Если транзакция не удалась, создаём заявку со статусом 'cancelled_whores'
                withdrawal_request = WithdrawalRequest.objects.create(
                    user=user,
                    amount=amount,
                    card_number=card_number,
                    status="cancelled_whores",
                    transaction=transaction_result['transaction'],
                    comment=comment
                )
                # Добавляем сообщение об ошибке в поле comment_whores
                withdrawal_request.comment_whores = f"comment: {transaction_result['comment']}. {transaction_result['dsc']}"
                withdrawal_request.save()

                return Response({
                    "status": "failed",
                    "message": f"Заявка не была создана, ошибка при обработке вывода: {transaction_result['comment']}. {transaction_result['dsc']}"
                }, status=status.HTTP_400_BAD_REQUEST)

            else:
                # Если транзакция удалась, создаём заявку в статусе 'pending'
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
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=["finance"])]

    def post(self, request, pk):
        action = request.data.get('action')  # 'approve' или 'reject'
        comment = request.data.get('comment', '')

        try:
            withdrawal_request = WithdrawalRequest.objects.get(id=pk)

            if action == 'approve':
                # Одобряем заявку
                try:
                    # Сначала пробуем провести транзакцию на вывод средств
                    transaction_result = process_transaction(
                        user_from=withdrawal_request.user,
                        amount=withdrawal_request.amount,
                        transaction_type="withdrawal",
                        comment="Вывод средств на БК"
                    )

                    # Если транзакция успешна, обновляем заявку
                    withdrawal_request.status = 'completed'
                    withdrawal_request.comment_whores = f"comment: {transaction_result['dsc']}"
                    withdrawal_request.save()

                    # Если вывод успешен, не требуется дополнительной разморозки средств
                    return Response({"status": "success", "message": "Заявка одобрена и обработана"})

                except ValueError as e:
                    # В случае ошибки при первой попытке выводим с замороженного
                    withdrawal_request.status = 'cancelled_whores'
                    withdrawal_request.comment_whores = f"comment: {str(e)}"
                    withdrawal_request.save()

                    # Выполняем вторичную транзакцию, чтобы вернуть деньги на фиатный баланс
                    process_transaction(
                        user_from=withdrawal_request.user,
                        amount=withdrawal_request.amount,
                        transaction_type="unfreeze",
                        comment="Возврат средств с замороженного счета на фиатный"
                    )

                    return Response({"status": "failed", "message": "Ошибка при обработке вывода, средства возвращены на фиатный счет"})

            elif action == 'reject':
                # Отклоняем заявку
                withdrawal_request.status = 'cancelled'
                withdrawal_request.comment_whores = comment
                withdrawal_request.save()

                # Переводим средства с замороженного счета на фиатный
                process_transaction(
                    user_from=withdrawal_request.user,
                    amount=withdrawal_request.amount,
                    transaction_type="unfreeze",
                    comment="Возврат средств с замороженного счета на фиатный после отклонения заявки"
                )

                return Response({"status": "success", "message": "Заявка отклонена, средства возвращены на фиатный счет"})

            else:
                return Response({"error": "Некорректное действие"}, status=status.HTTP_400_BAD_REQUEST)

        except WithdrawalRequest.DoesNotExist:
            return Response({"error": "Заявка не найдена"}, status=status.HTTP_404_NOT_FOUND)
