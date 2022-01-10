from django.test import TestCase
from rest_framework.test import APIClient

from account.models import User
from account.test_utils import UserFactory


class AccountTestCase(TestCase):
    auth_data = {
        "password": "SupperPassword123",
        "phone": "phone",
    }
    register_data = {
        "username": "phone",
        "first_name": "",
        "last_name": "",
    }

    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        # пытаемся создать юзера
        response = self.client.post('/account/users/', data={**self.auth_data, **self.register_data})
        self.assertEqual(response.status_code, 201)
        user = User.objects.latest('id')
        self.assertTrue(user)
        self.assertEqual(user.username, self.register_data['username'])
        self.assertEqual(user.phone, self.auth_data['phone'])

        # проверяем, что не можем создать юзера с тем же телефоном
        response = self.client.post('/account/users/', data=self.auth_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(user, User.objects.latest('id'))

        # в ответ на логин получаем токен
        response = self.client.post('/account/token/login', data=self.auth_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.json())

    def test_set_device_token(self):
        # обновляем токен устрйоства пользователю
        password = 'P@ssword'
        user = UserFactory(password=password)
        response = self.client.post('/account/token/login', data={
            'phone': user.phone,
            'password': password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.json())
        auth_token = response.json()['auth_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {auth_token}')

        self.assertEqual(user.device_token, '')
        response = self.client.post('/account/device/', data={
            'token': 'some new token'
        })
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.device_token, 'some new token')
