from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission



class RoleRequired:
    def __init__(self, roles, error_message="У вас нет доступа к этому ресурсу."):
        self.roles = roles
        self.error_message = error_message

    def __call__(self, view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Извлечение токена из заголовков
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return Response(
                    {"detail": "Токен не найден или некорректен."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            token = auth_header[7:]  # Извлекаем сам токен

            try:
                # Декодируем токен и получаем пользователя
                access_token = AccessToken(token)  # Проверка токена
                user_id = access_token['user_id']  # Извлекаем user_id из токена

                # Получаем вашу кастомную модель пользователя через get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)  # Получаем пользователя из базы данных
            except InvalidToken:
                return Response(
                    {"detail": "Токен невалиден."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            except Exception as e:
                return Response(
                    {"detail": f"Ошибка декодирования токена: {str(e)}"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Проверяем, есть ли у пользователя нужная роль
            if user.role not in self.roles:
                return Response(
                    {"detail": self.error_message},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Добавляем пользователя в request, если нужно для дальнейшей работы
            request.user = user

            return view_func(request, *args, **kwargs)

        return _wrapped_view




class IsAdmin(BasePermission):
    """
    Разрешение для администраторов
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'администратор'


class IsChecker(BasePermission):
    """
    Разрешение для проверяющих
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'проверяющий'


class IsCustomer(BasePermission):
    """
    Разрешение для проверяющих
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'заказчик'


class IsExecutor(BasePermission):
    """
    Разрешение для проверяющих
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'исполнитель'


class IsRole(BasePermission):
    """
    Разрешение для проверки, что роль пользователя соответствует одному из допустимых значений.
    """
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        # Проверяем, есть ли у пользователя роль в списке разрешенных
        return request.user and request.user.role in self.allowed_roles


class IsVerified(BasePermission):

    def __init__(self, required_verified=True):
        self.required_verified = required_verified

    def has_permission(self, request, view):
        # Если required_verified=True, проверяем наличие верификации
        if self.required_verified:
            return request.user and request.user.is_verification
        # Если required_verified=False, проверяем отсутствие верификации
        return request.user and not request.user.is_verification