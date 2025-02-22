from django.shortcuts import render
from functools import partial

from requests import Response
from rest_framework.views import APIView
from server.decorators import *
from payments.services import process_transaction
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *


class RankViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)
                          ]

    def get_queryset(self):
        """
        Возвращает ранги в зависимости от роли пользователя.
        Для исполнителей и заказчиков – разные наборы рангов.
        """
        user_role = self.request.user.role
        user_profile = self.request.user.profile

        current_rank = user_profile.rank

        if user_role == 'исполнитель':
            return Rank.objects.filter(rank_type='executor')
        elif user_role == 'заказчик':
            return Rank.objects.filter(rank_type='customer')
        else:
            return Rank.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Обрабатываем список рангов для пользователя с добавлением полей is_rank и is_can_rank
        """
        queryset = self.get_queryset()
        user = self.request.user  # Получаем пользователя

        # Сериализуем queryset с дополнительными полями
        serializer = RankSerializer(queryset, many=True, context={'user': user})
        return Response(serializer.data)


class RankPurchaseAPIView(APIView):
    permission_classes = [IsAuthenticated,
                          partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
                          partial(IsVerified)
                          ]


    def post(self, request, *args, **kwargs):

        user = request.user
        rank_id = request.data.get('rank_id')  # Получаем id ранга из запроса

        if not rank_id:
            return Response(
                {"error": "Не указано id ранга."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rank_to_buy = Rank.objects.get(id=rank_id)
        except Rank.DoesNotExist:
            return Response(
                {"error": "Указанный ранг не существует."},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = user.profile
        current_rank = profile.rank


        if rank_to_buy.rank_price <= current_rank.rank_price:
            return Response(
                {"error": "Пользователь уже имеет этот или более высокий ранг."},
                status=status.HTTP_400_BAD_REQUEST
            )


        if rank_to_buy.id != current_rank.id + 1:
            return Response(
                {"error": "Данный ранг недоступен. Необходимо сначала приобрести ранг ниже классом."},
                status=status.HTTP_400_BAD_REQUEST
            )


        transaction_response = process_transaction(user_from=user, amount=rank_to_buy.rank_price,
                                                   transaction_type="payment",
                                                   comment=f"Оплата ранга {rank_to_buy.rank_name}")

        if transaction_response["status"] == "failed":
            return Response(
                {"error": f"Не удалось выполнить покупку. {transaction_response['comment']}."
                          f" {transaction_response['dsc']}"},
                status=status.HTTP_400_BAD_REQUEST
            )


        profile.rank = rank_to_buy
        profile.save()


        return Response(
            {"message": f"Покупка ранга {rank_to_buy.rank_name} выполнена успешно."},
            status=status.HTTP_200_OK
        )
