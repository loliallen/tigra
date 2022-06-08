from datetime import datetime

import factory.fuzzy

from account.models import User, Invintation, Visit, SchedulerNotify, Condition


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('name')
    password = factory.PostGenerationMethodCall('set_password', 'user1!1')
    phone = factory.Faker('ssn', locale='ru_RU')
    is_staff = False


class InvintationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invintation

    value = factory.Sequence(lambda n: str(n).zfill(5))

    creator = factory.SubFactory(UserFactory)
    used_by = factory.SubFactory(UserFactory)
    is_used_by_creator = False


class VisitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Visit

    date = factory.LazyFunction(datetime.utcnow)
    duration = 3600
    is_active = False
    is_free = False
    user = factory.SubFactory(UserFactory)
    staff = factory.SubFactory(UserFactory)
    free_reason = None


class SchedulerNotifyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SchedulerNotify

    trigger = 'start'
    minute_offset = 0
    title = 'title'
    body = 'body'


class ConditionNotifyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Condition

    variable = 'visit.duration'
    comparator = '=='
    value = '30'
    scheduled_notify = factory.SubFactory(SchedulerNotifyFactory)
