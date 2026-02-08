import typing

from django.db.models import (
    QuerySet, Count, Max, ExpressionWrapper, F, Case, When,
    Value, CharField, DurationField, DateTimeField, Subquery, OuterRef
)
from django.db.models.functions import Cast, Concat

from apps.account.models import User
from apps.mobile.models import Visit


def users_all() -> QuerySet[User]:
    return User.objects.all()


def users_with_visits(queryset: typing.Optional[QuerySet[User]] = None) -> QuerySet[User]:
    last_visit = Visit.objects.filter(user=OuterRef('pk')).order_by('-date')
    if queryset is None:
        queryset = users_all()
    return queryset.annotate(
        visits_count=Count('visits_user'),
        # дата последнего визита
        last_visit_date=Subquery(last_visit.values_list("date")[:1]),
        # время конца последнего визита
        last_end=Max(
            ExpressionWrapper(
                (
                        F('visits_user__date') +
                        Cast(
                            # преобразуем хранящиеся в int секунды в timedelta и складываем с датой-время начала посещения
                            Concat(
                                Case(When(visits_user__duration__gt=0,
                                          then=F("visits_user__duration")), default=0),
                                Value(' seconds'),
                                output_field=CharField()
                            ),
                            output_field=DurationField()
                        )
                ),
                output_field=DateTimeField()
            )
        ),
        last_visit_store=Subquery(last_visit.values_list("store__address")[:1]),
        # child_name=StringAgg(Concat('children__name', Value(' '), Cast('children__birth_date', TextField())), delimiter=';'),
    )


def users_with_fio(queryset: typing.Optional[QuerySet[User]] = None) -> QuerySet[User]:
    if queryset is None:
        queryset = users_all()
    return queryset.annotate(
        fio=Concat(
            F("first_name"),
            Value(' '),
            F("last_name"),
        )
    )
