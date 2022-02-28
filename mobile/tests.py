from django.test import TestCase
from rest_framework.test import APIClient

from account.test_factories import InvintationFactory
from account.test_utils import get_auth_client


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
            self.assertEqual(len(resp_data['visits']), visit_num)
            self.assertEqual(resp_data['visits'][-1]['id'], visit_id)
            self.assertEqual(resp_data['visits'][-1]['is_free'], is_free)

    def test_free_visit_by_invintation(self):
        client_user, user = get_auth_client(self)
        new_client_user, new_user = get_auth_client(self)
        client_admin, admin = get_auth_client(self, is_admin=True)

        # создаем использованное приглашение
        invintation = InvintationFactory(creator=user, used_by=new_user)
        new_user.used_invintation = invintation
        new_user.save()

        self.assertEqual(invintation.used, True)
        self.assertEqual(invintation.visited, False)
        self.assertEqual(invintation.is_used_by_creator, False)

        # запрашиваем пользователем hash
        response = new_client_user.get('/mobile/visits/')
        new_client_hash = response.json()['hash']

        # берем админом id пользователя по хэшу
        response = client_admin.post('/mobile/visits/add/', data={'hash': new_client_hash})
        self.assertEqual(response.status_code, 200)
        new_user_id = response.json()['id']

        # создаем посещение и проверяем что оно создалось платным
        duration = 3600  # 1 час
        response = client_admin.put('/mobile/visits/add/', data={'user_id': new_user_id, 'duration': duration})
        self.assertEqual(response.status_code, 201)
        resp_data = response.json()
        self.assertEqual(resp_data['is_free'], False)

        # проверяем что его видит пользователь
        response = new_client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(len(resp_data['visits']), 1)
        self.assertEqual(resp_data['visits'][-1]['is_free'], False)

        self.assertEqual(invintation.used, True)
        self.assertEqual(invintation.visited, True)
        self.assertEqual(invintation.is_used_by_creator, False)

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
        self.assertEqual(resp_data['is_free'], True)
        self.assertEqual(resp_data['is_active'], True)
        self.assertEqual(resp_data['staff'], admin.id)

        # проверяем что его видит админ
        response = client_admin.get('/mobile/visits/add/')
        resp_data = response.json()
        self.assertEqual(resp_data[-1]['visiter'][0]['id'], user_id)
        self.assertEqual(resp_data[-1]['duration'], duration)
        self.assertEqual(resp_data[-1]['is_free'], True)
        self.assertEqual(resp_data[-1]['is_active'], True)
        self.assertEqual(resp_data[-1]['staff'], admin.id)

        # проверяем что его видит пользователь
        response = client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(len(resp_data['visits']), 1)
        self.assertEqual(resp_data['visits'][-1]['is_free'], True)

        invintation.refresh_from_db()
        self.assertEqual(invintation.used, True)
        self.assertEqual(invintation.visited, True)
        self.assertEqual(invintation.is_used_by_creator, True)
