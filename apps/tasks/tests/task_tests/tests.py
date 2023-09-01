from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.test import APITestCase
from apps.tasks.models import Task, TimeLog
from apps.tasks.views import TaskViewSet
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status

from apps.tasks.serializers import ShortTaskSerializer, AllCommentSerializer, TaskListSerializer, TaskAssignSerializer, TimeLogSerializer


# Create your tests here.


class TaskViewSetTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()
        self.view = TaskViewSet.as_view({'post': 'create', 'get': 'list'})
        self.user = User.objects.create_user(username='existing@example.com', first_name='Roman', last_name='Voitenko',
                                        email='existing@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.task = Task.objects.create(user=self.user, title="string", description="string", owner=self.user)

    def test_create_task(self):
        data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'user': self.user.id,
            'status': 'todo',
            'owner': self.user.id
        }
        request = self.factory.post('/tasks/', data, format='json')
        force_authenticate(request, user=self.user, token=self.token)
        response = self.view(request)
        self.assertEqual(response.status_code, 201)

    def test_create_task_invalid_data(self):
        data = {
            'title': '',
            'description': 'Test Description',
            'user': self.user.id,
            'status': 'todo',
            'owner': 999
        }
        request = self.factory.post('/tasks/', data, format='json')
        force_authenticate(request, user=self.user, token=self.token)
        response = self.view(request)
        self.assertEqual(response.status_code, 400)

    def test_get_serializer_class(self):
        view = TaskViewSet()
        view.action = 'retrieve'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, ShortTaskSerializer)
        view.action = 'comments'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, AllCommentSerializer)
        view.action = 'list'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TaskListSerializer)
        view.action = 'get_top_20_tasks_last_month'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TaskListSerializer)
        view.action = 'assign'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TaskAssignSerializer)
        view.action = 'time_logs_by_id'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TimeLogSerializer)
        view.action = 'create'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, view.serializer_class)

    def test_created_tasks(self):
        url = reverse('task-created')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_tasks(self):
        url = reverse('task-list')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_tasks(self):
        url = reverse('task-my')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_completed_tasks(self):
        url = reverse('task-completed')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_comments_tasks(self):
        url = reverse('task-comments', args=[self.task.pk])
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_time_logs_by_id_tasks(self):
        url = reverse('task-time-logs-by-id', args=[self.task.pk])
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_complete_task(self):
        self.task.owner = self.user
        self.task.save()
        url = reverse('task-complete', args=[self.task.pk])
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_assign_task(self):
        url = reverse('task-assign', args=[self.task.pk])
        self.client.force_authenticate(user=self.user)
        data = {
            "user": self.user.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_top_20_tasks_last_month(self):
        current_month = timezone.now().month
        for i in range(21):
            start_time = timezone.now() - relativedelta(days=i)
            if start_time.month == current_month:
                start_time = start_time - relativedelta(month=1)
            task = Task.objects.create(
                title=f'Test Task {i}',
                description=f'Test Description {i}',
                user=self.user,
                owner=self.user
            )
            TimeLog.objects.create(
                task=task,
                start_time=start_time,
                end_time=start_time + relativedelta(hours=1),
                user=self.user
            )
        url = reverse('task-get-top-20-tasks-last-month')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

