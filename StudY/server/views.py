from decimal import Decimal
from functools import partial

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from payments.models import *
from rank.models import *

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

from payments.services import process_transaction
from rank.services import check_user_rank

from .decorators import *


class RegisterGeneralInfoAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        referral_code = serializer.validated_data.pop('referral_code', None)
        user = serializer.save()
        try:
            if referral_code:
                referrer = User.objects.get(referral_code=referral_code)
                Referral.objects.create(referrer=referrer, referred=user)
        except User.DoesNotExist:
           pass


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
    #TODO отдавать id созданной заявки


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
                return  # Если реферер не верифицирован, не начисляем бонус

            # Получаем настройки бонусов в зависимости от роли
            if user.role == 'заказчик':
                referral_setting = ReferralSettings.objects.get(role='customer', level=1)
            elif user.role == 'исполнитель':
                referral_setting = ReferralSettings.objects.get(role='executor', level=1)
            else:
                raise serializers.ValidationError(f"Неизвестная роль для начисления бонуса: {user.role}")

            # Получаем бонусы для реферера
            bonus_to_referred = referral_setting.bonus_ref_user


            # Начисляем бонус рефереру
            if bonus_to_referred > 0:
                process_transaction(user_from=profile, amount=bonus_to_referred,
                                    rank_commission=check_user_rank(user=referrer, check_type='referral_bonus_self'),
                                    transaction_type='bonus_add',
                                    comment='Бонус за регистрацию по реферальной ссылке!',
                                    is_profile=True)

        except Referral.DoesNotExist:
            pass  # Если реферал не найден, ничего не делаем


class RegisterCustomerFeedbackInfoAPIView(generics.CreateAPIView):
    queryset = CustomerFeedback.objects.all()
    serializer_class = RegisterCustomerFeedbackSerializer
    permission_classes = [AllowAny]


class RegisterPortfolioInfoAPIView(generics.CreateAPIView):
    queryset = Portfolio.objects.all()
    serializer_class = RegisterPortfolioSerializer
    permission_classes = [AllowAny]


class StudentCardVerificationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, student_card_id):
        # Получаем объект заявителя
        student_card = StudentCard.objects.get(id=student_card_id)

        if student_card.user.role == 'исполнитель':
            available_statuses = ['Принят', 'Повторная проверка', 'Отклонена анкета исполнителя', 'Отправлен на доработку',
                                  'Отклонена верификация по СБ']
        elif student_card.user.role == 'заказчик':
            available_statuses = ['Принят', 'Повторная проверка', 'Отклонена верификация по СБ', 'Отправлен на доработку']
        else:
            return Response({"detail": "Роль пользователя не поддерживается для верификации."},
                            status=status.HTTP_400_BAD_REQUEST)

        immutable_statuses = ['Принят', 'Отклонена анкета исполнителя', 'Отклонена верификация по СБ',
                              'Отправлен на доработку']
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

            # Проверка уникальности номера студенческого билета
            if student_card_number and StudentCard.objects.filter(student_card_number=student_card_number).exclude(id=student_card.id).exists():
                return Response({"detail": "Студенческий билет с таким номером уже зарегистрирован."},
                                status=status.HTTP_400_BAD_REQUEST)

            student_card.status = status_veref
            student_card.save()

            if status_veref == 'Принят':
                student_card.student_card_number = student_card_number
                student_card.save()
                student_card.user.is_verification = True
                student_card.user.save()

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


class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        roles = [dict(id=i, value=role[0], label=role[1]) for i, role in enumerate(User.ROLE_CHOICES)]
        return Response(roles)


class VerificationStatusViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        statuses = [dict(id=i, value=status[0], label=status[1]) for i, status in enumerate(StudentCard.STATUS_CHOICES)]
        return Response(statuses)


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

        # Проверка, можно ли редактировать анкету
        if student_card.status in ['На проверке', 'Отклонена анкета исполнителя', 'Принят', 'Повторная проверка', '']:
            return Response({'detail': 'Редактирование анкеты невозможно в текущем статусе.'}, status=status.HTTP_403_FORBIDDEN)

        allowed_fields = {
            'first_name', 'last_name', 'vk_profile', 'telegram_username',
            'university', 'faculty', 'department', 'course', 'form_of_study',
            'photo', 'about_self', 'disciplines', 'customer_feedback', 'portfolio'
        }

        forbidden_fields = set(request.data.keys()) - allowed_fields
        if forbidden_fields:
            return Response({'detail': f'Редактирование следующих полей запрещено: {", ".join(forbidden_fields)}'},
                            status=status.HTTP_403_FORBIDDEN)

        profile = student_card.profile

        with transaction.atomic():
            # Валидация строковых полей
            for field in ['first_name', 'last_name', 'vk_profile', 'telegram_username', 'about_self']:
                if field in request.data:
                    if not isinstance(request.data[field], str):
                        return Response({f'detail': f'Поле "{field}" должно быть строкой.'},
                                        status=status.HTTP_400_BAD_REQUEST)
                    setattr(profile.user if field in ['first_name', 'last_name'] else profile, field, request.data[field])

            # Валидация ID-шников (должны быть целыми числами)
            for field in ['university', 'faculty', 'department', 'course', 'form_of_study']:
                if field in request.data:
                    try:
                        setattr(profile, f"{field}_id", int(request.data[field]))
                    except ValueError:
                        return Response({f'detail': f'Поле "{field}" должно быть целым числом.'},
                                        status=status.HTTP_400_BAD_REQUEST)

            # Валидация фото студенческого билета
            if 'photo' in request.FILES:
                student_card.photo = request.FILES['photo']

            # Валидация дисциплин
            if 'disciplines' in request.data:
                discipline_ids = request.data.get('disciplines')

                print(f"DEBUG: received disciplines: {discipline_ids}")  # Логируем входные данные

                if not isinstance(discipline_ids, list):
                    return Response({'detail': 'Дисциплины должны передаваться в виде массива ID.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                try:
                    discipline_ids = [int(d) for d in discipline_ids]
                except ValueError:
                    return Response({'detail': 'ID дисциплин должны быть числами.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Проверяем существование дисциплин в базе
                valid_disciplines = Discipline.objects.filter(id__in=discipline_ids)
                if len(valid_disciplines) != len(discipline_ids):
                    return Response({'detail': 'Некоторые ID дисциплин некорректны или отсутствуют в базе.'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Устанавливаем дисциплины пользователю
                profile.disciplines.set(valid_disciplines)

            # Валидация файлов (отзывы заказчиков и портфолио)
            for field, model in [('customer_feedback', CustomerFeedback), ('portfolio', Portfolio)]:
                if field in request.FILES:
                    files = request.FILES.getlist(field)

                    # Проверяем, что загруженные файлы действительно являются файлами
                    if not all(hasattr(f, 'read') for f in files):
                        return Response({'detail': f'Файлы для "{field}" должны быть корректными файлами.'},
                                        status=status.HTTP_400_BAD_REQUEST)

                    # Создаём новые объекты в соответствующей модели
                    for file in files:
                        model.objects.create(student_card=student_card, photo=file)

            # Обновление статуса анкеты
            student_card.status = 'Повторная проверка'

            profile.user.save()
            profile.save()
            student_card.save()

        return Response({'detail': 'Анкета успешно обновлена.'}, status=status.HTTP_200_OK)

    def replace_related_documents(self, student_card, model, files):
        """
        Полное обновление связанных документов (CustomerFeedback и Portfolio)
        """
        model.objects.filter(student_card=student_card).delete()  # Удаляем старые записи
        for file in files:
            model.objects.create(student_card=student_card, photo=file)


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
                referral_code = request.data.get('referrer_code')
                print(f'DEBUG реф код {referral_code}')
                if not user_serializer.is_valid():
                    raise ValueError(f"Ошибка в данных пользователя: {user_serializer.errors}")

                user = user_serializer.save()

                # 2️⃣ Обрабатываем реферальный код
                if referral_code:
                    try:
                        referrer = User.objects.get(referral_code=referral_code)
                        print(f'DEBUG Найден реферал {referrer}')
                        referral = Referral.objects.create(referrer=referrer, referred=user)
                    except ObjectDoesNotExist:
                        raise ValueError("Некорректный реферальный код")

                # 3️⃣ Создание профиля
                profile_data = request.data.get('profile', {})
                rank = Rank.objects.filter(rank_type='customer' if user.role == 'заказчик' else 'executor').first()
                if not rank:
                    raise ValueError(f"Ранг для роли {user.role} не найден.")

                profile_serializer = ProfileSerializer(data={**profile_data, 'user': user.id, 'rank': rank.id})
                if not profile_serializer.is_valid():
                    raise ValueError(f"Ошибка в данных профиля: {profile_serializer.errors}")

                profile = profile_serializer.save()

                # 4️⃣ Создание баланса
                Balance.objects.get_or_create(profile=profile)

                # 5️⃣ Обрабатываем загрузку портфолио и отзывов (если роль исполнителя)
                if user.role == 'исполнитель':
                    self._process_portfolio_and_feedback(user, profile, request)

                # 6️⃣ Начисляем реферальный бонус (только новому пользователю)
                print('Начинаю процедуру зачислений бонусов')
                self._process_referral_bonus(user, profile)
                print('Закончил процедуру зачислений бонусов')

                return Response({'message': 'Пользователь успешно зарегистрирован',
                                 'user_id': user.id,
                                 'profile_id': profile.id},
                                status=status.HTTP_201_CREATED)

        except ValueError as e:
            self._delete_user_objects(user, profile, referral, student_card, portfolio, feedback)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            self._delete_user_objects(user, profile, referral, student_card, portfolio, feedback)
            return Response({'error': f"Ошибка на сервере: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_referral_bonus(self, user, profile):
        """Начисление бонуса только новому пользователю"""
        try:
            print('DEBUG Начисление бонуса только новому пользователю')
            referral = Referral.objects.get(referred=user)
            referrer = referral.referrer  # Получаем реферера
            if not referrer.is_verification:
                print('реферер не верифицирован, не начисляем бонус')
                return  # Если реферер не верифицирован, не начисляем бонус

            # Получаем настройки бонуса только для нового пользователя
            if user.role == 'заказчик':
                referral_setting = ReferralSettings.objects.get(role='customer', level=1)
            elif user.role == 'исполнитель':
                referral_setting = ReferralSettings.objects.get(role='executor', level=1)
            else:
                raise ValueError(f"Неизвестная роль для начисления бонуса: {user.role}")

            # Бонус только новому пользователю
            bonus_to_referred = referral_setting.bonus_ref_user
            print(f'Перевод бонусов: {profile.user.username}'
                  f'Доп начисления (в %): {check_user_rank(user=referrer, check_type="referral_bonus_self")}')
            if bonus_to_referred > 0:
                process_transaction(user_from=profile, amount=bonus_to_referred,
                                    rank_commission=check_user_rank(user=referrer, check_type='referral_bonus_self'),
                                    transaction_type='bonus_add',
                                    comment='Бонус за регистрацию по реферальной ссылке!',
                                    is_profile=True)

        except Referral.DoesNotExist:
            pass  # Если реферал не найден, ничего не делаем

    def _process_portfolio_and_feedback(self, user, profile, request):
        """Обработка загрузки портфолио и отзывов"""
        portfolio_data = request.data.get('portfolio', [])
        for item in portfolio_data:
            portfolio_serializer = RegisterPortfolioSerializer(
                data={**item, 'user': user.id, 'profile': profile.id})
            if not portfolio_serializer.is_valid():
                raise ValueError(f"Ошибка в данных портфолио: {portfolio_serializer.errors}")
            portfolio_serializer.save()

        feedback_data = request.data.get('customer_feedback', [])
        for item in feedback_data:
            feedback_serializer = RegisterCustomerFeedbackSerializer(
                data={**item, 'user': user.id, 'profile': profile.id})
            if not feedback_serializer.is_valid():
                raise ValueError(f"Ошибка в данных обратной связи: {feedback_serializer.errors}")
            feedback_serializer.save()

    def _delete_user_objects(self, user, profile, referral=None, student_card=None, portfolio=None, feedback=None):
        """Удаление всех объектов, если регистрация не удалась"""
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

class StudentCardStatusView(APIView):
    permission_classes = [AllowAny]
    """
    API-эндпоинт для получения статуса анкеты пользователя.
    """

    def post(self, request, *args, **kwargs):
        """
        Получение статуса анкеты по пользователю.
        Ожидаемый параметр в теле запроса: `user_id`
        """

        # Проверяем, передан ли user_id
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'Необходимо передать user_id.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, существует ли пользователь
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, существует ли анкета (StudentCard)
        try:
            student_card = StudentCard.objects.get(user=user)
        except StudentCard.DoesNotExist:
            return Response({'detail': 'Анкета не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        # Возвращаем статус анкеты
        return Response({'status': student_card.status}, status=status.HTTP_200_OK)


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

        if user.is_verification:
            user.count_auth += 1
            user.save()
        if user.count_auth > 1:
            is_start_auth = False
        else:
            if user.is_verification:
                is_start_auth = True
            else:
                is_start_auth = False

        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_verification": user.is_verification,
            'is_start_auth': is_start_auth
        }

        return Response(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data,
            },
            status=status.HTTP_200_OK
        )