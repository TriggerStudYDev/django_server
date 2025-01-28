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


class RegisterEducationInfoAPIView(generics.CreateAPIView):
    queryset = StudentCard.objects.all()
    serializer_class = StudentCardRegisterSerializer
    permission_classes = [AllowAny]

    # def create(self, request, *args, **kwargs):
    #     """
    #     Переопределение метода create, чтобы можно было обработать вложенные данные и вернуть подробный ответ.
    #     """
    #     # Преобразуем данные из запроса
    #     data = request.data
    #
    #     # Проверьте, есть ли все необходимые поля в запросе
    #     if 'user' not in data or 'profile' not in data:
    #         return Response({"detail": "User and profile are required."}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     # Создаем сериализатор и валидация данных
    #     serializer = self.get_serializer(data=data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     # Сохраняем данные в базе
    #     student_card = serializer.save()
    #
    #     # Возвращаем созданную запись вместе с вложенными объектами (customer_feedback, portfolio)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegisterProfileInfoAPIView(generics.CreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        profile = serializer.save()
        user = profile.user
        if not user:
            raise serializers.ValidationError("Профиль должен быть связан с пользователем.")

        Balance.objects.get_or_create(user=user)


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

        # Проверка роли проверяющего
        # if request.user.role != 'проверяющий':
        #     return Response({"detail": "Только проверяющий может верифицировать заявки."},
        #                     status=status.HTTP_403_FORBIDDEN)

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

        # Для остальных ролей доступ запрещен
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