from rest_framework import serializers
from .models import *


class RankDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RankDescription
        fields = ['privilege_type', 'description_text']


# Сериализатор для ранга
class RankSerializer(serializers.ModelSerializer):
    descriptions = RankDescriptionSerializer(many=True, read_only=True)
    is_rank = serializers.SerializerMethodField()
    is_can_rank = serializers.SerializerMethodField()

    class Meta:
        model = Rank
        fields = ['id', 'rank_name', 'rank_price', 'rank_image_url', 'descriptions', 'is_rank', 'is_can_rank']

    def get_is_rank(self, obj):
        """
        Метод для определения, купил ли пользователь данный ранг.
        """
        user = self.context.get('user')  # Получаем пользователя из контекста
        current_rank = user.profile.rank  # Получаем текущий ранг пользователя
        return obj == current_rank  # Проверяем, равен ли ранг текущему рангу пользователя

    def get_is_can_rank(self, obj):
        """
        Метод для проверки, доступен ли данный ранг для покупки.
        """
        user = self.context.get('user')  # Получаем пользователя из контекста
        current_rank = user.profile.rank  # Получаем текущий ранг пользователя
        return obj.rank_price > current_rank.rank_price and obj.id == current_rank.id + 1