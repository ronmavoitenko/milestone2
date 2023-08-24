from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.serializers import UserSerializer, UserListSerializer
from apps.users.views import UserViewSet


class UserViewSetTestCase(TestCase):
    fixtures = ['users']

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = UserViewSet.as_view({'post': 'register', 'get': 'users_list'})
        self.data = {
            'first_name': 'Roman',
            'last_name': 'Voitenco',
            'email': '7@example.com',
            'password': 'test_password'
        }

    def test_register_new_user(self):
        request = self.factory.post(reverse('register'), self.data)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_invalid_data(self):
        invalid_data = {
            'first_name': 'Roman',
            'last_name': 'Voitenko',
            'email': 'invalid_email',
            'password': 'testpassword'
        }
        request = self.factory.post(reverse('register'), invalid_data)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_users_list(self):
        url = reverse('users_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
