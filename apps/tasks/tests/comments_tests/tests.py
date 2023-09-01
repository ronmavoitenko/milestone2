from django.shortcuts import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from apps.tasks.models import Task
from rest_framework.authtoken.models import Token

from apps.tasks.serializers import CreateCommentSerializer
from apps.tasks.views import CommentViewSet


class CommentViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='existing@example.com', first_name='Roman', last_name='Voitenko',
                                             email='existing@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            user=self.user,
            owner=self.user
        )

    def test_get_serializer_class(self):
        view = CommentViewSet()
        view.action = 'create'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, CreateCommentSerializer)
        view.action = 'list'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, view.serializer_class)

    def test_create_comments(self):
        self.task.owner = self.user
        self.task.save()
        url = reverse('comments-list')
        data = {
            'text': 'Test Comment',
            'task': self.task.id
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
