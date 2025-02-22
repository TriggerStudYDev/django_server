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
        fields = ['id', 'user', 'amount', 'status', 'date_submitted', 'comment', 'card_number', ]


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


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type = serializers.CharField(source='get_transaction_type_display')
    status = serializers.CharField(source='get_status_display')
    comment = serializers.CharField(default="Отсутствует", allow_blank=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S")
    dsc = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'status', 'comment', 'created_at', 'dsc']