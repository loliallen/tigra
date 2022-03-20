from django.test import TestCase
from rest_framework.test import APIClient

from account.test_factories import InvintationFactory, VisitFactory
from account.test_utils import get_auth_client
from mobile.models import FreeReason


class VisitTest(TestCase):
    COUNT_TO_FREE_VISIT = 4

    def setUp(self):
        self.client = APIClient()

    def test_create_simple_paid_visit(self):
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

    def create_visit(self, is_free, free_reason, client_admin, client_user, user_id, visit_count, admin):
        """ функция создания и проверки визитов - используется в других теста, сама по себе тестом не является """

        # создаем посещение и проверяем что оно создалось
        duration = 3600  # 1 час
        response = client_admin.put('/mobile/visits/add/', data={'user_id': user_id, 'duration': duration})
        self.assertEqual(response.status_code, 201)
        resp_data = response.json()
        self.assertEqual(resp_data['is_free'], is_free)
        self.assertEqual(resp_data['free_reason'], free_reason)

        # проверяем что его видит админ
        response = client_admin.get('/mobile/visits/add/')
        resp_data = response.json()
        # self.assertEqual(len(resp_data), visit_count)
        self.assertEqual(resp_data[-1]['visiter'][0]['id'], user_id)
        self.assertEqual(resp_data[-1]['staff'], admin.id)
        self.assertEqual(resp_data[-1]['is_free'], is_free)
        self.assertEqual(resp_data[-1]['free_reason'], free_reason)
        visit_id = resp_data[-1]['id']

        # проверяем что его видит пользователь
        response = client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(len(resp_data['visits']), visit_count)
        self.assertEqual(resp_data['visits'][-1]['id'], visit_id)
        self.assertEqual(resp_data['visits'][-1]['is_free'], is_free)
        self.assertEqual(resp_data['visits'][-1]['free_reason'], free_reason)

    def test_free_visit(self):
        client_user, user = get_auth_client(self)
        client_admin, admin = get_auth_client(self, is_admin=True)
        free_visit_num = self.COUNT_TO_FREE_VISIT + 1  # каждый пятый визит должен быть бесплатным
        user_id = user.id

        # пробуем дойти до бесплатного визита 3 раза и потом еще один визит
        for visit_num in range(1, free_visit_num * 3 + 1):
            # создаем посещение и проверяем что оно создалось
            is_free = bool(visit_num % free_visit_num == 0)
            free_reason = FreeReason.COUNT if is_free else None
            self.create_visit(is_free, free_reason, client_admin, client_user, user_id, visit_num, admin)

    def test_free_visit_by_invintation(self):
        client_user, user = get_auth_client(self)
        new_client_user, new_user = get_auth_client(self)
        client_admin, admin = get_auth_client(self, is_admin=True)

        # создаем использованное приглашение
        invintation = InvintationFactory(creator=user, used_by=new_user)
        new_user.used_invintation = invintation
        new_user.save()

        # проверяем что купон теперь использован, но не активирован и создателем не использован
        self.assertEqual(invintation.used, True)
        self.assertEqual(invintation.visited, False)
        self.assertEqual(invintation.is_used_by_creator, False)

        # создаем платный визит новым пользователем
        VisitFactory(user=new_user, staff=admin, is_free=False)

        # проверяем что купон теперь использован и активирован, но создателем не использован
        self.assertEqual(invintation.used, True)
        self.assertEqual(invintation.visited, True)
        self.assertEqual(invintation.is_used_by_creator, False)

        # создаем посещение которое должно стать бесплатным потому использованному пригласительному купону
        user_id = user.id
        is_free = True
        free_reason = FreeReason.INVITE
        visit_num = 1
        self.create_visit(is_free, free_reason, client_admin, client_user, user_id, visit_num, admin)

        # проверяем что купон теперь использован, активирован и использован создателем
        invintation.refresh_from_db()
        self.assertEqual(invintation.used, True)
        self.assertEqual(invintation.visited, True)
        self.assertEqual(invintation.is_used_by_creator, True)

    def test_free_visit_by_count_and_invite(self):
        """ тест на бесплатный визит по инвайту не будет сбивать счетчик бесплатных визитов по количеству """
        client_user, user = get_auth_client(self)
        new_client_user, new_user = get_auth_client(self)
        client_admin, admin = get_auth_client(self, is_admin=True)

        # создаем несколько платных визитов пользователем
        paid_visit_created = self.COUNT_TO_FREE_VISIT - 1
        for i in range(paid_visit_created):
            VisitFactory(user=user, staff=admin, is_free=False)

        response = client_user.get('/account/about/me/')
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertEqual(resp_data['count_to_free_visit'], 1)
        self.assertEqual(resp_data['free_reason'], FreeReason.COUNT)

        # создаем использованное приглашение
        invintation = InvintationFactory(creator=user, used_by=new_user)
        new_user.used_invintation = invintation
        new_user.save()

        # создаем платный визит новым пользователем
        VisitFactory(user=new_user, staff=admin, is_free=False)

        # проверяем, что теперь у пользователя след. бесплатный визит по инвайт коду
        response = client_user.get('/account/about/me/')
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertEqual(resp_data['count_to_free_visit'], 0)
        self.assertEqual(resp_data['free_reason'], FreeReason.INVITE)

        user_id = user.id
        is_free = True
        free_reason = FreeReason.INVITE
        visit_num = paid_visit_created + 1
        self.create_visit(is_free, free_reason, client_admin, client_user, user_id, visit_num, admin)

        # проверяем что у пользователя осталось одно посещение до бесплатного
        response = client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(resp_data['count_to_free_visit'], 1)
        self.assertEqual(resp_data['free_reason'], FreeReason.COUNT)

        # создаем еще один платный визит
        is_free = False
        free_reason = None
        visit_num = paid_visit_created + 2
        self.create_visit(is_free, free_reason, client_admin, client_user, user_id, visit_num, admin)

        # проверяем что у пользователя следущее посещение бесплатное
        response = client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(resp_data['count_to_free_visit'], 0)
        self.assertEqual(resp_data['free_reason'], FreeReason.COUNT)

        # создаем еще один визит -  он должен стать бесплтаным
        is_free = True
        free_reason = FreeReason.COUNT
        visit_num = paid_visit_created + 3
        self.create_visit(is_free, free_reason, client_admin, client_user, user_id, visit_num, admin)

        # проверяем что у пользователя обнулился счетчик
        response = client_user.get('/account/about/me/')
        resp_data = response.json()
        self.assertEqual(resp_data['count_to_free_visit'], self.COUNT_TO_FREE_VISIT)
        self.assertEqual(resp_data['free_reason'], FreeReason.COUNT)
