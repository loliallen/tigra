import datetime
from typing import Optional, Tuple

from django.db.models import Count
from django.utils.timezone import localtime

from apps.mobile.models import Visit, FreeReason


VISITS_TO_FREE = 4  # сколько нужно сделать платных визитов чтобы следующий был бесплатным


def check_not_used_invite(user) -> Optional['Invintation']:
    invintation: 'Invintation' = (
        user.invintation_creator.filter(used_by__isnull=False)
            .annotate(num_visits=Count('used_by__visits_user'))
            .filter(num_visits__gt=0, is_used_by_creator=False)
            .last()
    )
    return invintation


def get_visits_to_count(user):
    last_free = user.visits_user.filter(free_reason=FreeReason.COUNT, is_confirmed=True).last()
    visits = user.visits_user.filter(is_free=False, is_confirmed=True)
    days_ago_30 = localtime() - datetime.timedelta(days=30)
    if last_free:
        after = max(days_ago_30, last_free.date)
    else:
        after = days_ago_30
    visits = visits.filter(date__gt=after)
    return visits


def count_to_free_visit(user) -> Tuple[int, FreeReason]:
    if check_not_used_invite(user):
        return 0, FreeReason.INVITE
    cnt = VISITS_TO_FREE - get_visits_to_count(user).count()
    return cnt if cnt >= 0 else 0, FreeReason.COUNT


def set_visit_if_free(visit_obj: Visit):
    """

    :param visit_obj: Новый объект визита
    :param user: пользователь
    :return:
    """
    user = visit_obj.user

    # проверка на бесплатный визит по количеству платных посещений
    visits_to_count = get_visits_to_count(user).count()
    if VISITS_TO_FREE - visits_to_count <= 0:
        visit_obj.is_free = True
        visit_obj.free_reason = FreeReason.COUNT
        visit_obj.is_active = False  # костыль для отображения на фронте как бесплатного пятого посещения
        return
    # ищем приглашение по которому пришел пользователь, сделал хотя бы один визит и которое создатель еще не использовал
    invintation: 'Invintation' = check_not_used_invite(user)
    if invintation is not None:
        visit_obj.is_free = True
        visit_obj.free_reason = FreeReason.INVITE
        invintation.is_used_by_creator = True
        invintation.save()
        return
