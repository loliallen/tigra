import typing

from django.db.models import (
    QuerySet, ExpressionWrapper, F, Value, CharField,
    DurationField, DateTimeField
)
from django.db.models.functions import Cast, Concat

from apps.mobile.models import Visit


def visits_all() -> QuerySet[Visit]:
    return Visit.objects.all()


def visits_with_end_at(queryset: typing.Optional[QuerySet[Visit]] = None) -> QuerySet[Visit]:
    if queryset is None:
        queryset = visits_all()
    return queryset.annotate(
        end_at=ExpressionWrapper(
            (
                    F('date') +
                    Cast(
                        # преобразуем хранящиеся в int секунды в timedelta и складываем с датой-время начала посещения
                        Concat(
                            F("duration"),
                            Value(' seconds'),
                            output_field=CharField()
                        ),
                        output_field=DurationField()
                    )
            ),
            output_field=DateTimeField()
        ),
    )
