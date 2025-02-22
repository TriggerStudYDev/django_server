from django.core.exceptions import ObjectDoesNotExist

from .models import RankSettings


from django.core.exceptions import ObjectDoesNotExist

def check_user_rank(user, check_type, is_profile=False):
    """
    Проверяет привилегии пользователя на основе его ранга.
    """
    try:
        if is_profile:
            profile=user
        else:
            profile = user.profile
    except ObjectDoesNotExist:
        print(f"Ошибка: Профиль для пользователя {user} не найден.")
        return False

    # Получаем настройки ранга через ранг профиля
    try:
        rank_settings = RankSettings.objects.get(rank=profile.rank)
    except RankSettings.DoesNotExist:
        print(f"Ошибка: Настройки ранга для пользователя {user} (ранг: {profile.rank}) не найдены.")
        return False

    # Проверяем наличие запрашиваемого атрибута
    if hasattr(rank_settings, check_type):
        field = getattr(rank_settings, check_type, None)

        if field is None:
            print(f"Ошибка: Поле {check_type} не найдено в настройках ранга {profile.rank}.")
            return False

        return field  # Может быть True, False или числовое значение

    print(f"Ошибка: Атрибут {check_type} отсутствует в модели RankSettings.")
    return False