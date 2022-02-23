from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from account.models import User
from account.test_utils import get_auth_client


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

    def test_set_device_token(self):
        # обновляем токен устрйоства пользователю
        client, user = get_auth_client(self)
        self.assertEqual(user.device_token, '')
        response = client.post('/account/device/', data={
            'token': 'some new token'
        })
        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.device_token, 'some new token')

    def test_info(self):
        # проверяем наличие инфы о пользователе
        client, user = get_auth_client(self)
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
        client, user = get_auth_client(self)
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


class VisitTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_visit(self):
        client_user, user = get_auth_client(self)
        client_admin, admin = get_auth_client(self, is_admin=True)

        # запрашиваем пользователем hash
        response = client_user.get('/mobile/visits/')
        hash = response.json()['hash']

        # берем админом id пользователя по хэшу
        response = client_admin.post('/mobile/visits/add/', data={'hash': hash})
        self.assertEqual(response.status_code, 200)
        user_id = response.json()['id']

        # создаем посещение и проверяем что оно создалось
        duration = 3600  # 1 час
        response = client_admin.put('/mobile/visits/add/', data={'user_id': user_id, 'duration': duration})
        self.assertEqual(response.status_code, 201)
        resp_data = response.json()
        self.assertEqual(resp_data['duration'], duration)
        self.assertEqual(resp_data['is_free'], False)
        self.assertEqual(resp_data['is_active'], True)
        self.assertEqual(resp_data['staff'], admin.id)

        # проверяем что его видит админ
        response = client_admin.get('/mobile/visits/add/')
        resp_data = response.json()
        self.assertEqual(resp_data[0]['visiter'][0]['id'], user_id)
        self.assertEqual(resp_data[0]['duration'], duration)
        self.assertEqual(resp_data[0]['is_free'], False)
        self.assertEqual(resp_data[0]['is_active'], True)
        self.assertEqual(resp_data[0]['staff'], admin.id)

        # проверяем что его видит пользователь
        response = client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(len(resp_data['visits']), 1)

    def test_free_visit(self):
        client_user, user = get_auth_client(self)
        client_admin, admin = get_auth_client(self, is_admin=True)
        free_visit_num = 5  # каждый пятый визит должен быть бесплатным

        # пробуем дойти до бесплатного визита 3 раза и потом еще один визит
        for visit_num in range(1, free_visit_num * 3 + 1):
            # запрашиваем пользователем hash
            response = client_user.get('/mobile/visits/')
            hash = response.json()['hash']

            # берем админом id пользователя по хэшу
            response = client_admin.post('/mobile/visits/add/', data={'hash': hash})
            self.assertEqual(response.status_code, 200)
            user_id = response.json()['id']

            # создаем посещение и проверяем что оно создалось
            duration = 3600  # 1 час
            is_free = bool(visit_num % free_visit_num == 0)
            response = client_admin.put('/mobile/visits/add/', data={'user_id': user_id, 'duration': duration})
            self.assertEqual(response.status_code, 201)
            resp_data = response.json()
            self.assertEqual(resp_data['is_free'], is_free)

            # проверяем что его видит админ
            response = client_admin.get('/mobile/visits/add/')
            resp_data = response.json()
            self.assertEqual(len(resp_data), visit_num)
            self.assertEqual(resp_data[-1]['visiter'][0]['id'], user_id)
            self.assertEqual(resp_data[-1]['staff'], admin.id)
            self.assertEqual(resp_data[-1]['is_free'], is_free)
            visit_id = resp_data[-1]['id']

            # проверяем что его видит пользователь
            response = client_user.get('/account/about/me/')
            resp_data = response.json()
            # если это визит перед бесплатным - то создастся два сразу два визита которые мы тут увидим
            is_empty_visit_created = visit_num % free_visit_num == free_visit_num - 1
            if is_empty_visit_created:
                self.assertEqual(len(resp_data['visits']), visit_num + 1)
                self.assertEqual(resp_data['visits'][-2]['id'], visit_id)
                self.assertEqual(resp_data['visits'][-2]['is_free'], False)
                self.assertEqual(resp_data['visits'][-1]['id'], visit_id + 1)
                self.assertEqual(resp_data['visits'][-1]['is_free'], True)
            else:
                self.assertEqual(len(resp_data['visits']), visit_num)
                self.assertEqual(resp_data['visits'][-1]['id'], visit_id)
                self.assertEqual(resp_data['visits'][-1]['is_free'], is_free)

    # TODO: добавить тестов на бесплатный визит по приглашению
