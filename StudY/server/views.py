from functools import partial

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db import transaction

from .decorators import *


class ExampleViewSet(ModelViewSet):
    queryset = ExampleModel.objects.all()
    serializer_class = ExampleModelSerializer
    permission_classes = [AllowAny]


class TestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestViews.objects.all()
    serializer_class = TestViewsSerializer
    permission_classes = [AllowAny]


class TestViewCreateAPIView(generics.CreateAPIView):
    queryset = TestViews.objects.all()
    serializer_class = TestViewsSerializer
    permission_classes = [AllowAny]


class RegisterGeneralInfoAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        referral_code = serializer.validated_data.pop('referral_code', None)
        user = serializer.save()
        if referral_code:
            referrer = User.objects.get(referral_code=referral_code)
            Referral.objects.create(referrer=referrer, referred=user)


class ReferralTokenCheckAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        referral_code = request.query_params.get('referral_code')

        if not referral_code:
            return Response({"error": "Параметр 'referral_code' обязателен."}, status=400)

        user = get_object_or_404(User, referral_code=referral_code)

        # Проверяем верификацию реферера
        if not user.is_verification:
            return Response(
                {"error": "Реферальная ссылка неактивна, пригласивший пользователь еще не прошел верификацию."},
                status=403
            )

        return Response({
            "username": user.username,
            "role": user.role,
            "rank": user.profile.rank.rank_name if user.profile and user.profile.rank else None  # Проверка на наличие ранга
        })


class RegisterEducationInfoAPIView(generics.CreateAPIView):
    queryset = StudentCard.objects.all()
    serializer_class = StudentCardRegisterSerializer
    permission_classes = [AllowAny]


class RegisterProfileInfoAPIView(generics.CreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.validated_data.get('user')

        if not user:
            raise serializers.ValidationError("Профиль должен быть связан с пользователем.")

        # Назначаем ранг в зависимости от роли пользователя
        if user.role == 'заказчик':
            rank = Rank.objects.filter(rank_type='customer').first()  # Ранг для заказчика
        elif user.role == 'исполнитель':
            rank = Rank.objects.filter(rank_type='executor').first()  # Ранг для исполнителя
        else:
            raise serializers.ValidationError(f"Невозможно определить ранг для роли {user.role}")

        # Проверяем, найден ли ранг
        if not rank:
            raise serializers.ValidationError(f"Ранг для роли {user.role} не найден.")

        # Создаем профиль с установленным рангом
        profile = serializer.save(rank=rank)

        # Создаем баланс пользователя, если его нет
        Balance.objects.get_or_create(profile=profile)


        # Проверяем наличие реферальной связи
        try:
            referral = Referral.objects.get(referred=user)
            referrer = referral.referrer  # Получаем реферера
            if not referrer.is_verification:
                return
            # Получаем настройки бонусов в зависимости от роли
            if user.role == 'заказчик':
                referral_setting = ReferralSettings.objects.get(role='customer', level=1)
            elif user.role == 'исполнитель':
                referral_setting = ReferralSettings.objects.get(role='executor', level=1)
            else:
                raise serializers.ValidationError(f"Неизвестная роль для начисления бонуса: {user.role}")

            # Начисляем бонус рефереру
            bonus_to_referred = referral_setting.bonus_ref_user

            with transaction.atomic():

                # Начисление бонуса приглашенному пользователю
                Transaction.objects.create(
                    profile=profile,
                    amount=bonus_to_referred,
                    transaction_type="bonus_add",
                    comment="Бонус за регистрацию по реферальной ссылке",
                    status="completed"
                )

                # Обновляем баланс пользователей
                profile.balance.fiat_balance += bonus_to_referred
                profile.balance.save()



        except Referral.DoesNotExist:
           pass


class RegisterCustomerFeedbackInfoAPIView(generics.CreateAPIView):
    queryset = CustomerFeedback.objects.all()
    serializer_class = RegisterCustomerFeedbackSerializer
    permission_classes = [AllowAny]

    # def perform_create(self, serializer):
    #     user = self.request.user
    #
    #     if not hasattr(user, 'profile'):
    #         raise serializers.ValidationError("У пользователя отсутствует связанный профиль.")
    #
    #         # Проверяем роль пользователя
    #     if user.role != 'исполнитель':
    #         raise serializers.ValidationError(
    #             "Добавление документов доступно только для пользователей с ролью 'исполнитель'!"
    #         )


class RegisterPortfolioInfoAPIView(generics.CreateAPIView):
    queryset = Portfolio.objects.all()
    serializer_class = RegisterPortfolioSerializer
    permission_classes = [AllowAny]

    # def perform_create(self, serializer):
    #     user = self.request.user
    #
    #     # if not hasattr(user, 'profile'):
    #     #     raise serializers.ValidationError("У пользователя отсутствует связанный профиль.")
    #
    #         # Проверяем роль пользователя
    #     if user.role != 'исполнитель':
    #         raise serializers.ValidationError(
    #             f"Добавление документов доступно только для пользователей с ролью 'исполнитель'!"
    #             f"Ваш польвзоатель: {user}"
    #         )


class StudentCardVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, student_card_id):
        # Получаем объект заявителя
        student_card = StudentCard.objects.get(id=student_card_id)


        if student_card.user.role == 'исполнитель':
            available_statuses = ['Принят', 'Отклонена анкета исполнителя', 'Отправлен на доработку',
                                  'Отклонена верификация по СБ']
        elif student_card.user.role == 'заказчик':
            available_statuses = ['Принят', 'Отклонена верификация по СБ', 'Отправлен на доработку']
        else:
            return Response({"detail": "Роль пользователя не поддерживается для верификации."},
                            status=status.HTTP_400_BAD_REQUEST)

        immutable_statuses = ['Принят', 'Отклонена анкета исполнителя']
        if student_card.status in immutable_statuses:
            return Response(
                {"detail": f"Статус '{student_card.status}' нельзя изменить."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StudentCardVerificationSerializer(data=request.data)
        if serializer.is_valid():
            status_veref = serializer.validated_data['status']
            student_card_number = serializer.validated_data.get('student_card_number', None)
            comment = serializer.validated_data.get('comment', None)

            # Проверка на доступность статуса
            if status_veref not in available_statuses:
                return Response({"detail": "Этот статус не доступен для текущего типа пользователя."},
                                status=status.HTTP_400_BAD_REQUEST)
            if student_card_number is None and status_veref == 'Принят':
                return Response({"detail": "При одобрении заявки необходимо ввести номер студенческого билета."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Обновляем статус заявки
            student_card.status = status_veref
            student_card.save()

            # Обновление активности пользователя
            if status_veref == 'Принят':
                student_card.student_card_number = student_card_number
                student_card.user.is_verification = True
                student_card.user.save()

            # Добавление комментария, если он есть
            if comment:
                StudentCardComment.objects.create(
                    student_card=student_card,
                    comment=comment,
                    author=request.user
                )

            return Response({"detail": "Статус заявки успешно обновлен."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentCardViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = StudentCard.objects.prefetch_related(
        'customerfeedback_set', 'portfolio_set', 'comments'
    )
    serializer_class = StudentCardSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['проверяющий', 'исполнитель', 'заказчик']),
        partial(IsVerified, required_verified=False)
    ]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['заказчик', 'исполнитель']:
            return StudentCard.objects.filter(user=user)
        if user.role == 'проверяющий':
            queryset = super().get_queryset()

            role = self.request.query_params.get('role', None)
            status = self.request.query_params.get('status', None)

            if status:
                queryset = queryset.filter(status=status)
            if role:
                queryset = queryset.filter(user__role=role)

            return queryset

        return StudentCard.objects.none()

    def retrieve(self, request, *args, **kwargs):
        """
        Переопределяем метод для ограничения доступа к заявкам других пользователей.
        """
        instance = self.get_object()

        # Проверка доступа для заказчиков и исполнителей
        if request.user.role in ['заказчик', 'исполнитель'] and instance.user != request.user:
            return Response(
                {"detail": "У вас нет доступа к этой анкете."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)


class StudentCardUpdateView(APIView):
    permission_classes = [
        IsAuthenticated,
        partial(IsRole, allowed_roles=['исполнитель', 'заказчик']),
        partial(IsVerified, required_verified=False)
    ]

    def put(self, request, *args, **kwargs):
        try:
            student_card = StudentCard.objects.get(user=request.user)
        except StudentCard.DoesNotExist:
            return Response({'detail': 'Анкета не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StudentCardUpdateSerializer(student_card, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Анкета успешно обновлена.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomerFeedback.objects.all()
    serializer_class = CustomerFeedbackSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        student_card_id = self.request.query_params.get('student_card_id')
        if student_card_id:
            return self.queryset.filter(student_card_id=student_card_id)
        return self.queryset


class PortfolioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        student_card_id = self.request.query_params.get('student_card_id')
        if student_card_id:
            return self.queryset.filter(student_card_id=student_card_id)
        return self.queryset


class StudentCardCommentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StudentCardComment.objects.all()
    serializer_class = StudentCardCommentSerializer
    permission_classes = [AllowAny]


# Отображение информационных данных для учебного учреждения
class UniversityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [AllowAny]


class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        university_id = self.request.query_params.get('university_id')
        if university_id:
            return self.queryset.filter(university_id=university_id)
        return self.queryset


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        faculty_id = self.request.query_params.get('faculty_id')
        if faculty_id:
            return self.queryset.filter(faculty_id=faculty_id)
        return self.queryset


class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        department_id = self.request.query_params.get('department_id')
        if department_id:
            return self.queryset.filter(department_id=department_id)
        return self.queryset


class FormOfStudyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormOfStudy.objects.all()
    serializer_class = FormOfStudySerializer
    permission_classes = [AllowAny]


class UnifiedRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UnifiedRegistrationSerializer
    permission_classes = [AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Формируем ответ
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "detail": "Регистрация успешно выполнена. Аккаунт ожидает проверки модератором.",
                "user_id": user.id,
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )




class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = None
        profile = None
        referral = None
        student_card = None
        portfolio = None
        feedback = None

        try:
            with transaction.atomic():
                # 1️⃣ Создание пользователя
                user_serializer = UserSerializer(data=request.data.get('user'))
                referral_code = request.data.get('referral_code')

                if not user_serializer.is_valid():
                    raise ValueError(user_serializer.errors)

                user = user_serializer.save()

                # 2️⃣ Обрабатываем реферальный код
                if referral_code:
                    try:
                        referrer = User.objects.get(referral_code=referral_code)
                        referral = Referral.objects.create(referrer=referrer, referred=user)
                    except User.DoesNotExist:
                        raise ValueError("Некорректный реферальный код")

                # 3️⃣ Создание профиля
                profile_data = request.data.get('profile', {})
                rank = Rank.objects.filter(rank_type='customer' if user.role == 'заказчик' else 'executor').first()
                if not rank:
                    raise ValueError(f"Ранг для роли {user.role} не найден.")

                profile_serializer = ProfileSerializer(data={**profile_data, 'user': user.id, 'rank': rank.id})
                if not profile_serializer.is_valid():
                    raise ValueError(profile_serializer.errors)

                profile = profile_serializer.save()

                # 4️⃣ Создание баланса
                Balance.objects.get_or_create(profile=profile)

                # 5️⃣ Создание студенческого билета
                student_card_data = request.data.get('student_card', {})
                student_card_serializer = StudentCardRegisterSerializer(
                    data={**student_card_data, 'user': user.id, 'profile': profile.id}
                )

                if not student_card_serializer.is_valid():
                    raise ValueError(student_card_serializer.errors)
                student_card = student_card_serializer.save()

                # 6️⃣ Обрабатываем загрузку портфолио и обратных связей, если роль исполнителя
                if user.role == 'исполнитель':
                    portfolio_data = request.data.get('portfolio', [])
                    for item in portfolio_data:
                        portfolio_serializer = RegisterPortfolioSerializer(data={**item, 'user': user.id, 'profile': profile.id})
                        if not portfolio_serializer.is_valid():
                            raise ValueError(portfolio_serializer.errors)
                        portfolio = portfolio_serializer.save()

                    feedback_data = request.data.get('customer_feedback', [])
                    for item in feedback_data:
                        feedback_serializer = RegisterCustomerFeedbackSerializer(data={**item, 'user': user.id, 'profile': profile.id})
                        if not feedback_serializer.is_valid():
                            raise ValueError(feedback_serializer.errors)
                        feedback = feedback_serializer.save()

                self._process_referral_bonus(user, profile)

                return Response({'message': 'Пользователь успешно зарегистрирован'}, status=status.HTTP_201_CREATED)

        except ValueError as e:
            self._delete_user_objects(user, profile, referral, student_card, portfolio, feedback)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            self._delete_user_objects(user, profile, referral, student_card, portfolio, feedback)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_referral_bonus(self, user, profile):
        """Обработка реферального бонуса"""
        try:
            referral = Referral.objects.get(referred=user)
            referrer = referral.referrer  # Получаем реферера
            if not referrer.is_verification:
                return
            # Получаем настройки бонусов в зависимости от роли
            if user.role == 'заказчик':
                referral_setting = ReferralSettings.objects.get(role='customer', level=1)
            elif user.role == 'исполнитель':
                referral_setting = ReferralSettings.objects.get(role='executor', level=1)
            else:
                raise serializers.ValidationError(f"Неизвестная роль для начисления бонуса: {user.role}")

            # Начисляем бонус рефереру
            bonus_to_referred = referral_setting.bonus_ref_user

            with transaction.atomic():
                # Начисление бонуса приглашенному пользователю
                Transaction.objects.create(
                    profile=profile,
                    amount=bonus_to_referred,
                    transaction_type="bonus_add",
                    comment="Бонус за регистрацию по реферальной ссылке",
                    status="completed"
                )

                # Обновляем баланс пользователей
                profile.balance.fiat_balance += bonus_to_referred
                profile.balance.save()

        except Referral.DoesNotExist:
            pass

    def _delete_user_objects(self, user, profile, referral=None, student_card=None, portfolio=None, feedback=None):
        if referral:
            referral.delete()  # Удаляем реферал, если был создан
        if profile:
            profile.delete()  # Удаляем профиль, если был создан
        if student_card:
            student_card.delete()  # Удаляем студенческий билет, если был создан
        if portfolio:
            portfolio.delete()  # Удаляем портфолио, если было создано
        if feedback:
            feedback.delete()  # Удаляем обратную связь, если была создана
        if user:
            user.delete()  # Удаляем пользователя, если был создан

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def get_ip_address(self, request):
        """Функция для получения IP-адреса из запроса"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"detail": "Необходимо указать логин и пароль."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем IP-адрес клиента
        ip_address = self.get_ip_address(request)

        # Проверяем, не заблокирован ли пользователь
        failed_attempt = FailedLoginAttempt.objects.filter(ip_address=ip_address).first()
        if failed_attempt and failed_attempt.is_locked():
            return Response(
                {"detail": "Ваш аккаунт заблокирован на 10 минут после 5 неудачных попыток входа."},
                status=status.HTTP_403_FORBIDDEN
            )

        user = authenticate(username=username, password=password)
        if not user:
            failed_attempt, created = FailedLoginAttempt.objects.get_or_create(
                ip_address=ip_address
            )
            failed_attempt.increment_attempts()

            if failed_attempt.attempts >= 5:
                failed_attempt.lock_account()
                return Response(
                    {"detail": "Ваш аккаунт заблокирован на 10 минут после 5 неудачных попыток входа."},
                    status=status.HTTP_403_FORBIDDEN
                )

            return Response(
                {"detail": "Неверный логин и/или пароль."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        failed_attempt, created = FailedLoginAttempt.objects.get_or_create(
            ip_address=ip_address
        )
        failed_attempt.reset_attempts()

        if user.role in ['заказчик', 'исполнитель']:
            try:
                student_card = StudentCard.objects.get(user=user)

                if student_card.status == 'Принят':
                    # Пользователь успешно верифицирован
                    pass

                elif student_card.status in ['Отклонена верификация по СБ', 'Отправлен на доработку']:
                    # Сообщаем, что доступна только страница редактирования анкеты
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)

                    user_data = {
                        "id": user.id,
                        "username": user.username,
                        "role": user.role,
                        "is_verification": user.is_verification,
                    }

                    return Response(
                        {
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "user": user_data,
                            "detail": "Ваша анкета требует корректировок. Доступна только страница редактирования анкеты.",
                        },
                        status=status.HTTP_200_OK
                    )

                elif student_card.status == 'Отклонена анкета исполнителя':
                    return Response(
                        {"detail": "Ваша анкета отклонена: анкета исполнителя отклонена."},
                        status=status.HTTP_403_FORBIDDEN
                    )

                elif student_card.status == 'На проверке':
                    return Response(
                        {"detail": "Ваша анкета еще на проверке."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            except StudentCard.DoesNotExist:
                return Response(
                    {"detail": "Анкета не найдена."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Генерация токенов для всех остальных случаев
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_verification": user.is_verification,
        }

        return Response(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data,
            },
            status=status.HTTP_200_OK
        )