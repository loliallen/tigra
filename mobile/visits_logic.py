from django.db.models import Count

from account.models import Visit, Invintation


VISITS_TO_FREE = 4


def set_visit_if_free(visit_obj: Visit):
    """

    :param visit_obj: Новый объект визита
    :param user: пользователь
    :return:
    """
    user = visit_obj.user
    count = user.visits_user.count()
    # проверка на бесплатный визит
    if count != 0 and (count + 1) % (VISITS_TO_FREE + 1) == 0:
        visit_obj.is_free = True
        visit_obj.is_active = False  # костыль для отображения на фронте как бесплатного пятого посещения
        return
    # ищем приглашение по которому пришел пользователь, сделал хотя бы один визит и которое создать еще не использовал
    invintation: Invintation = user.invintation_creator.filter(used_by__isnull=False).annotate(num_visits=Count('used_by__visits_user')).filter(num_visits__gt=0, is_used_by_creator=False).last()
    if invintation is not None:
        visit_obj.is_free = True
        invintation.is_used_by_creator = True
        invintation.save()
        return
