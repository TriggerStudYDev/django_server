from rest_framework import serializers
from .models import *
from server.models import Discipline, Department


class DisciplineSerializer(serializers.ModelSerializer):
    executor_count = serializers.SerializerMethodField()

    class Meta:
        model = Discipline
        fields = ['id', 'name', 'photo', 'executor_count']

    def get_executor_count(self, obj):
        return ExecutorDiscipline.objects.filter(discipline=obj).count()


class ProfileDisciplineSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='name')
    department_photo = serializers.ImageField(source='photo')
    disciplines = DisciplineSerializer(many=True)

    class Meta:
        model = Department
        fields = ['id', 'department_name', 'department_photo', 'disciplines']