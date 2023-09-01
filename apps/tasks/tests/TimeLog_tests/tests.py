from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from apps.tasks import serializers
from apps.tasks.serializers import StopTimeLogSerializer, TimeLogSerializer, CreateTimeLogSerializer
from apps.tasks.models import Task, TimeLog
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.shortcuts import reverse

from apps.tasks.views import TimerViewSet


class CreateTimeLogSerializerTestCase(APITestCase):

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
        view = TimerViewSet()
        view.action = 'create'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, view.serializer_class)
        view.action = 'stop'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, StopTimeLogSerializer)
        view.action = 'add_time_log_manually'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TimeLogSerializer)

    def test_start_and_stop_time_log(self):
        url = reverse('timer-list')
        data = {
            'task': self.task.id
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse('timer-stop')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validate_task_with_running_timer(self):
        self.client.force_authenticate(user=self.user)
        TimeLog.objects.create(task=self.task, end_time=None, user=self.user)
        data = {
            "task": self.task.id,
        }
        serializer = CreateTimeLogSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("A timer is already running for this task", str(context.exception))

    def test_validate_task_with_no_running_timer(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "task": self.task.id,
        }
        serializer = StopTimeLogSerializer(data=data)
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("No running timer found for this task", str(context.exception))

    def test_add_time_log_manually(self):
        url = reverse('timer-add-time-log-manually')
        data = {
            'task': self.task.id,
            'start_time': "2023-09-01 12:01",
            'end_time': "2023-09-01 12:11",
            'duration': 10
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_time_logged_last_month(self):
        url = reverse('timer-get-time-logged-last-month')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
