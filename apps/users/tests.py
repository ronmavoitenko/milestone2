from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from apps.users.views import UserViewSet
from apps.users.serializers import UserSerializer
from django.db.utils import IntegrityError


class UserViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserViewSet.as_view({'post': 'create'})

    def test_create_user(self):
        data = {
            'first_name': 'Roman',
            'last_name': 'Voitenco',
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        request = self.factory.post('/users/', data, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email=data['email'])
        self.assertEqual(user.email, data['email'])

    # def test_get_serializer_class_create(self):
    #     self.view.action = 'create'
    #     serializer_class = self.view.get_serializer_class()
    #     self.assertEqual(serializer_class, UserSerializer)

    def test_create_user_invalid_data(self):
        data = {
            'first_name': 'Roman',
            'last_name': 'Voitenko',
            'email': 'invalidemail',
            'password': 'testpassword'
        }
        request = self.factory.post('/users/', data, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_user_duplicate_email(self):
        User.objects.create_user(username='existing@example.com', first_name='Roman', last_name='Voitenko', email='existing@example.com', password='testpassword')
        data = {
            'first_name': 'Roman',
            'last_name': 'Voitenko',
            'email': 'existing@example.com',
            'password': 'testpassword'
        }
        request = self.factory.post('/users/', data, format='json')
        with self.assertRaises(IntegrityError):
            self.view(request)

    def test_create_user_without_password(self):
        data = {
            'first_name': 'Roman',
            'last_name': 'Voitenko',
            'email': 'test@example.com',
        }
        request = self.factory.post('/users/', data, format='json')
        response = self.view(request)
        self.assertEqual(response.status_code, 400)

