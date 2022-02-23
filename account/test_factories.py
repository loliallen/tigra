import factory.fuzzy

from account.models import User, Invintation


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

    creator = None
    used = False
    visited = False