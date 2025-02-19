from django.core.exceptions import ObjectDoesNotExist

from .models import RankSettings


def check_user_rank(user, check_type):
    """
    Функция для проверки привилегий пользователя на основе его ранга.
    """
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        print(f"Профиль для пользователя {user} не найден")
        return False

    try:
        rank_settings = RankSettings.objects.get(type_role=user.role, rank=profile.rank)
    except RankSettings.DoesNotExist:
        print(f"Настройки ранга для пользователя {user} не найдены")
        return False

    print(f"RankSettings для {user}: {rank_settings}")
    if check_type in RankSettings._meta.get_fields():
        field = getattr(rank_settings, check_type, None)

        if field is None:
            print(f"Поле {check_type} не найдено в настройках ранга для {user}")
            return False

        if isinstance(field, bool):
            return field

        elif isinstance(field, int):
            return field

    return False