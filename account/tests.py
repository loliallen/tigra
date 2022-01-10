from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from account.models import User
from account.test_utils import UserFactory


class RegisterTest(TestCase):
    auth_data = {
        "password": "SupperPassword123",
        "phone": "phone",
    }
    register_data = {
        "username": "phone",
        "first_name": "",
        "last_name": "",
    }

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


class AccountTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def get_auth_client(self):
        client = APIClient()
        password = 'P@ssword'
        user = UserFactory(password=password)
        response = client.post('/account/token/login', data={
            'phone': user.phone,
            'password': password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.json())
        auth_token = response.json()['auth_token']
        client.credentials(HTTP_AUTHORIZATION=f'Token {auth_token}')
        return client, user

    def test_set_device_token(self):
        # обновляем токен устрйоства пользователю
        client, user = self.get_auth_client()
        self.assertEqual(user.device_token, '')
        response = client.post('/account/device/', data={
            'token': 'some new token'
        })
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.device_token, 'some new token')

    def test_info(self):
        # проверяем наличие инфы о пользователе
        client, user = self.get_auth_client()
        response = client.get('/account/about/me/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['visits'], [])
        self.assertEqual(data['children'], [])
        self.assertEqual(data['used_invintation'], None)
        self.assertEqual(data['my_invintations'], [])
        self.assertIn('phone', data)
        self.assertIn('username', data)
        self.assertEqual(data['phone_confirmed'], False)
        self.assertEqual(data['device_token'], '')

    @patch('account.controller._send_code')
    def test_confirm_phone(self, send_code_mock):
        # подтверждение телефона
        client, user = self.get_auth_client()
        response = client.get('/account/about/me/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['phone_confirmed'], False)

        response = self.client.post('/account/confirm/', data={
            'phone': user.phone
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(send_code_mock.call_args.args[0], user.phone)
        code = send_code_mock.call_args.args[1]

        response = self.client.get('/account/confirm/', data={
            'id': data['id'],
            'code': '',
        })
        self.assertEqual(response.status_code, 403)

        response = self.client.get('/account/confirm/', data={
            'id': data['id'],
            'code': code,
        })
        self.assertEqual(response.status_code, 200)
