import factory.fuzzy

from account.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('name')
    password = factory.PostGenerationMethodCall('set_password', 'user1!1')
    phone = factory.Faker('ssn', locale='ru_RU')
