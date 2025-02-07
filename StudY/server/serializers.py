from rest_framework import serializers
from django.db import transaction
from .models import *


class ExampleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleModel
        fields = '__all__'


class TestViewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestViews
        fields = ['voice', 'dsc', 'date_start', 'data_end', 'is_active']


# Сериализаторы для регистрации пользователей (исполнитель или заказчик)
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'role', 'is_active', 'last_activity']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ProfileRegisterSerializer(serializers.ModelSerializer):
    user = UserRegisterSerializer()

    class Meta:
        model = Profile
        fields = ['user', 'photo', 'university', 'faculty', 'department', 'disciplines', 'form_of_study', 'vk_profile', 'telegram_username']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserRegisterSerializer.create(UserRegisterSerializer(), validated_data=user_data)
        profile = Profile.objects.create(user=user, **validated_data)
        return profile


class PortfolioRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['student_card', 'photo']

    def create(self, validated_data):
        student_card = validated_data.get('student_card')
        portfolio = Portfolio.objects.create(student_card=student_card, **validated_data)
        return portfolio


class CustomerFeedbackRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = ['student_card', 'photo']

    def create(self, validated_data):
        student_card = validated_data.get('student_card')
        feedback = CustomerFeedback.objects.create(student_card=student_card, **validated_data)
        return feedback


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ('id', 'name')


class FacultySerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ('id', 'name', 'university')


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'faculty')


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ('id', 'name', 'department')


class FormOfStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = FormOfStudy
        fields = ('id', 'name')


def validate_referral_code(value):
    if value and not User.objects.filter(referral_code=value).exists():
        raise serializers.ValidationError("Реферальный код не найден.")
    return value


class UserSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Реферальный код пригласившего пользователя"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password', 'role', 'referral_code')
        extra_kwargs = {'password': {'write_only': True}, 'referral_code': {'read_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('username', 'first_name', 'last_name', 'email', 'password', 'role', "is_verification", "referral_code")
#         extra_kwargs = {'password': {'write_only': True}, 'referral_code': {'read_only': True}}
#
#     def create(self, validated_data):
#         user = User.objects.create_user(**validated_data)
#         return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('user', 'rank', 'university', 'faculty', 'department', 'disciplines', 'form_of_study', 'vk_profile',
                  'telegram_username')


class RegisterCustomerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = ('photo', 'student_card')


class RegisterPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ('photo', 'student_card')


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFeedback
        fields = ('photo',)


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ('photo',)


class StudentCardCommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()  # Для отображения имени автора

    class Meta:
        model = StudentCardComment
        fields = ('comment', 'created_at', 'author')


class StudentCardRegisterSerializer(serializers.ModelSerializer):
    # customer_feedback = CustomerFeedbackSerializer(many=True, source='customerfeedback_set')
    # portfolio = PortfolioSerializer(many=True, source='portfolio_set')

    class Meta:
        model = StudentCard
        fields = ('user', 'profile', 'photo', 'about_self',
                  # 'customer_feedback', 'portfolio'
                  )

    # def create(self, validated_data):
    #     # Извлечение вложенных данных
    #     customer_feedback_data = validated_data.pop('customerfeedback_set', [])
    #     portfolio_data = validated_data.pop('portfolio_set', [])
    #
    #     # Создание основной записи StudentCard
    #     student_card = StudentCard.objects.create(**validated_data)
    #
    #     # Создание обратных отзывов
    #     for feedback in customer_feedback_data:
    #         CustomerFeedback.objects.create(student_card=student_card, **feedback)
    #
    #     # Создание портфолио
    #     for portfolio_item in portfolio_data:
    #         Portfolio.objects.create(student_card=student_card, **portfolio_item)
    #
    #     return student_card



class StudentCardSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    profile = ProfileSerializer()

    customer_feedback = CustomerFeedbackSerializer(many=True, source='customerfeedback_set')
    portfolio = PortfolioSerializer(many=True, source='portfolio_set')
    comments = StudentCardCommentSerializer(many=True)


    class Meta:
        model = StudentCard
        fields = ('id',
            'user', 'profile', 'student_card_number', 'about_self', 'photo', 'status',
            'customer_feedback', 'portfolio', 'comments'
        )


class UnifiedRegistrationSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    student_card = StudentCardRegisterSerializer()
    customer_feedback = RegisterCustomerFeedbackSerializer(many=True, required=False)
    portfolio = RegisterPortfolioSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password', 'role',
                  'profile', 'student_card', 'customer_feedback', 'portfolio')
        extra_kwargs = {'password': {'write_only': True}}

    @transaction.atomic
    def create(self, validated_data):
        # Извлекаем вложенные данные
        profile_data = validated_data.pop('profile')
        student_card_data = validated_data.pop('student_card')
        customer_feedback_data = validated_data.pop('customer_feedback', [])
        portfolio_data = validated_data.pop('portfolio', [])

        # Создаем пользователя
        user = User.objects.create_user(**validated_data)
        user.is_verification = False  # По умолчанию аккаунт не активен
        user.save()

        # Создаем профиль
        profile = Profile.objects.create(user=user, **profile_data)

        # Создаем студенческий билет
        student_card = StudentCard.objects.create(user=user, profile=profile, **student_card_data)

        # Добавляем обратные связи и портфолио
        for feedback in customer_feedback_data:
            CustomerFeedback.objects.create(student_card=student_card, **feedback)
        for portfolio_item in portfolio_data:
            Portfolio.objects.create(student_card=student_card, **portfolio_item)

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)





class StudentCardVerificationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StudentCard.STATUS_CHOICES)
    comment = serializers.CharField(required=False)
    student_card_number = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        status = attrs.get('status')
        comment = attrs.get('comment')


        # Если статус "Отправлен на доработку" или "Отклонен", комментарий обязателен
        if status in ['Отправлен на доработку', 'Отклонена анкета исполнителя'] and not comment:
            raise serializers.ValidationError("Комментарий обязателен при отклонении или отправке на доработку.")

        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'university',
            'faculty',
            'department',
            'disciplines',
            'form_of_study',
            'vk_profile',
            'telegram_username',
        ]
        extra_kwargs = {
            'vk_profile': {'required': False},
            'telegram_username': {'required': False},
        }


class StudentCardUpdateSerializer(serializers.ModelSerializer):
    profile = ProfileUpdateSerializer()
    feedback = serializers.PrimaryKeyRelatedField(
        queryset=CustomerFeedback.objects.all(), required=False
    )
    portfolio = serializers.PrimaryKeyRelatedField(
        queryset=Portfolio.objects.all(), required=False
    )

    class Meta:
        model = StudentCard
        fields = [
            'about_self',
            'photo',
            'profile',
            'feedback',
            'portfolio',
            'status',
        ]
        extra_kwargs = {
            'status': {'read_only': True},
        }

    def validate(self, data):

        user = self.instance.user
        if user.role == 'заказчик' and ('feedback' in data or 'portfolio' in data):
            raise serializers.ValidationError("Поле 'feedback' и 'portfolio' недоступны для роли 'заказчик'.")

        if self.instance.status in ['На проверке', 'Отклонена анкета исполнителя', 'Принят']:
            raise serializers.ValidationError("Редактирование анкеты невозможно в текущем статусе.")

        return data

    def update(self, instance, validated_data):
        # Обновление связанных данных профиля
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            profile_serializer = ProfileUpdateSerializer(instance.profile, data=profile_data, partial=True)
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        # Обновление отзывов и портфолио для исполнителя
        if instance.user.role == 'исполнитель':
            feedback = validated_data.pop('feedback', None)
            portfolio = validated_data.pop('portfolio', None)
            if feedback:
                instance.feedback = feedback
            if portfolio:
                instance.portfolio = portfolio

        # Обновление остальных полей анкеты
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Изменение статуса заявки на "На проверке"
        instance.status = 'На проверке'
        instance.save()
        return instance







