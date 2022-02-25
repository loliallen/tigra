import json
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from account.models import User
from account.test_factories import InvintationFactory
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
        self.assertEqual(response.status_code, 201, response.json())
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
        self.assertEqual(response.status_code, 200, response.json())
        self.assertIn('auth_token', response.json())

    def test_register_with_invintation_code(self):
        # пытаемся создать юзера
        invintation = InvintationFactory()
        data = {**self.auth_data, **self.register_data, "inv_code": invintation.value}
        response = self.client.post('/account/users/', data)
        self.assertEqual(response.status_code, 201)
        user = User.objects.latest('id')
        self.assertTrue(user)
        self.assertEqual(user.username, self.register_data['username'])
        self.assertEqual(user.phone, self.auth_data['phone'])
        self.assertEqual(user.used_invintation.id, invintation.id)


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

    def test_update_info(self):
        client, user = get_auth_client(self)
        response = client.put('/account/manage/', data={
            "username": "not_a_number",
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "test@email.ru",
            "children": json.dumps([{
                "add": "",
                "data": {
                    "sex": "М",
                    "age": 10,
                    "name": "Даша",
                },
            }])
        })
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertEqual(resp_data["username"], "not_a_number")
        self.assertEqual(resp_data["first_name"], "Тест")
        self.assertEqual(resp_data["last_name"], "Тестов")
        self.assertEqual(resp_data["email"], "test@email.ru")
        self.assertEqual(resp_data["email"], "test@email.ru")
        self.assertEqual(resp_data["children"][0]["sex"], "М")
        self.assertEqual(resp_data["children"][0]["age"], 10)
        self.assertEqual(resp_data["children"][0]["name"], "Даша")
        child_id = resp_data["children"][0]["id"]

        response = client.put('/account/manage/', data={
            "children": json.dumps([{
                "id": child_id,
                "updates": {
                    "sex": "Ж",
                    "age": 11,
                    "name": "Катя",
                },
            }])
        })
        resp_data = response.json()
        self.assertEqual(resp_data["children"][0]["sex"], "Ж")
        self.assertEqual(resp_data["children"][0]["age"], 11)
        self.assertEqual(resp_data["children"][0]["name"], "Катя")

        response = client.put('/account/manage/', data={
            "children": json.dumps([{
                "delete": True,
                "id": child_id
            }])
        })
        resp_data = response.json()
        self.assertEqual(len(resp_data["children"]), 0)


class InviteTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_invite(self):
        client, user = get_auth_client(self)
        new_client, new_user = get_auth_client(self)

        # Создаем код для приглашения
        response = client.post('/account/invite/')
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertEqual(resp_data['used'], False)
        self.assertEqual(resp_data['visited'], False)
        self.assertEqual(resp_data['creator'], user.id)
        invite_id, value = resp_data['id'], resp_data['value']

        # Проверяем наличие кода у себя
        response = client.get('/account/invite/')
        resp_data = response.json()
        self.assertEqual(resp_data[0]['id'], invite_id)
        self.assertEqual(resp_data[0]['value'], value)
        self.assertEqual(resp_data[0]['used'], False)
        self.assertEqual(resp_data[0]['visited'], False)
        self.assertEqual(resp_data[0]['creator'], user.id)

        # Проверяем наличие кода новым пользователем ???
        response = new_client.put('/account/use/invintation/', data={'code': value})
        resp_data = response.json()
        self.assertEqual(resp_data['id'], invite_id)
        self.assertEqual(resp_data['value'], value)
        self.assertEqual(resp_data['used'], False)
        self.assertEqual(resp_data['visited'], False)
        self.assertEqual(resp_data['creator'], user.id)

        # Апрувим этот код новым пользователем
        response = new_client.post('/account/use/invintation/', data={'code': value})
        resp_data = response.json()
        self.assertEqual(resp_data['id'], invite_id)
        self.assertEqual(resp_data['value'], value)
        self.assertEqual(resp_data['used'], True)
        self.assertEqual(resp_data['visited'], False)
        self.assertEqual(resp_data['creator'], user.id)
        new_user.refresh_from_db()
        self.assertEqual(new_user.used_invintation.id, invite_id)
