from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.test import APITestCase
from apps.tasks.models import Task, TimeLog
from apps.tasks.views import TaskViewSet, CommentViewSet, TimerViewSet
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.tasks.serializers import ShortTaskSerializer, AllCommentSerializer, TaskListSerializer, TaskAssignSerializer, \
    TimeLogSerializer, CreateCommentSerializer, StopTimeLogSerializer, CreateTimeLogSerializer


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

    def test_get_serializer_class_taskviewset(self):
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
        view.action = 'top'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TaskListSerializer)
        view.action = 'assign'
        serializer_class = view.get_serializer_class()
        self.assertEqual(serializer_class, TaskAssignSerializer)
        view.action = 'time_logs'
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
        url = reverse('task-time-logs', args=[self.task.pk])
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
        url = reverse('task-top')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_serializer_class_commentviewset(self):
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

    def test_get_serializer_class_timerviewset(self):
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
