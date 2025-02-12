from decimal import Decimal

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from server.models import *


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'amount', 'status', 'date_submitted', 'comment', 'card_number']


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = ['fiat_balance', 'frozen_balance', 'bonus_balance', 'forfeited_balance']


class BonusTransferSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    comment = serializers.CharField(max_length=255, required=False)

    def validate(self, data):
        # Проверим, существует ли пользователь с таким username
        try:
            recipient_user = User.objects.get(username=data['username'])
            recipient_profile = recipient_user.profile
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким username не найден.")

        data['recipient_profile'] = recipient_profile
        return data