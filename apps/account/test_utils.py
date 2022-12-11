import factory.fuzzy
from rest_framework.test import APIClient

from apps.account.test_factories import UserFactory


def get_auth_client(test_case, is_admin=False):
    client = APIClient()
    password = 'P@ssword'
    user = UserFactory(password=password, is_staff=is_admin)
    response = client.post('/account/token/login', data={
        'phone': user.phone,
        'password': password,
    })
    test_case.assertEqual(response.status_code, 200)
    test_case.assertIn('auth_token', response.json())
    auth_token = response.json()['auth_token']
    client.credentials(HTTP_AUTHORIZATION=f'Token {auth_token}')
    return client, user
