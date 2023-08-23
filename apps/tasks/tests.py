import mock as mock
from dateutil.relativedelta import relativedelta
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils import timezone

from apps.tasks.views import TaskViewSet, CommentViewSet, TimerViewSet
from apps.tasks.models import Task, Comment, TimeLog

from apps.tasks.serializers import TaskDetailsByIdSerializer, TaskListSerializer, \
    AllCommentSerializer, TimeLogSerializer


# Create your tests here.

class TaskTestCase(TestCase):
    fixtures = ["tasks"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(email='user1@email.com')
        self.task = Task.objects.create(title='Test Task', description='Test Description', user=self.user,
                                        owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_task(self):
        data = {
            'title': 'Task Test',
            'description': 'Description Test'
        }
        response = self.client.post('/tasks/create-task/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.last()
        self.assertEqual(task.title, 'Task Test')
        self.assertEqual(task.description, 'Description Test')
        self.assertEqual(task.user.id, self.user.id)
        self.assertEqual(task.owner.id, self.user.id)
        self.assertEqual(task.status, 'todo')

    def test_create_task_bad_request(self):
        data = {
            'description': 'Description Test'
        }
        response = self.client.post('/tasks/create-task/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_created_tasks(self):
        response = self.client.get('/tasks/created_tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_data = response.data[0]
        self.assertEqual(task_data['title'], 'Test Task 1')
        self.assertEqual(task_data['id'], 1)

    def test_task_details_by_id(self):
        response = self.client.get(f'/tasks/task_details_by_id/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TaskDetailsByIdSerializer(self.task)
        self.assertEqual(response.data, serializer.data)

    @mock.patch('apps.tasks.views.Task.objects')
    def test_task_details_access_forbidden(self, mock_task_objects):
        mock_task = mock.Mock()
        mock_task_objects.get.return_value = mock_task
        mock_task.user = mock.Mock()
        mock_task.owner = mock.Mock()

        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"id": 18}
        request.user = mock.Mock()

        response = view.task_details_by_id(request, task_id=request.data["id"])

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"error": "You do not have permission to view this task."})

    def test_task_details_by_id_exception(self):
        view = TaskViewSet()
        with mock.patch('apps.tasks.views.Task.objects.get') as mock_get:
            mock_get.side_effect = Task.DoesNotExist
            request = mock.Mock()
            request.data = {"id": 1}
            request.user = mock.Mock()
            response = view.task_details_by_id(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task not found"})

    def test_search_task_by_title(self):
        title = 'Test Task 2'
        response = self.client.post('/tasks/search_task_by_title/', {'title': title})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tasks = Task.objects.filter(title__icontains=title, user=self.user) | \
                Task.objects.filter(title__icontains=title, owner=self.user)
        serializer = TaskListSerializer(tasks, many=True)

        self.assertEqual(response.data, serializer.data)

    @mock.patch('apps.tasks.views.Task.objects')
    def test_search_task_by_title_exception(self, mock_task_objects):
        mock_task_objects.filter.side_effect = Task.DoesNotExist
        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"title": "Test Title"}
        request.user = mock.Mock()
        response = view.search_task_by_title(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "There are no tasks with this title"})

    def test_my_tasks(self):
        response = self.client.get('/tasks/my_tasks')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = Task.objects.filter(owner=self.user)
        serializer = TaskListSerializer(tasks, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_completed_tasks(self):
        response = self.client.get('/tasks/completed_tasks')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = Task.objects.filter(status='done', user=self.user) | \
                Task.objects.filter(status='done', owner=self.user)
        serializer = TaskListSerializer(tasks, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_assign_task_to_user(self):
        new_user = User.objects.create_user(first_name='John', last_name='Doe', email='john@example.com',
                                            password='testpassword', username='john@example.com')
        response = self.client.post('/tasks/assign_task_to_user', {'task_id': self.task.id, 'user_id': new_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.owner, new_user)

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_assign_task_to_user_task_not_found(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.assign_task_to_user(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task not found"})

    @mock.patch('apps.tasks.models.Task.objects.get')
    @mock.patch('apps.tasks.models.User.objects.get')
    def test_assign_task_to_user_user_not_found(self, mock_user_get, mock_task_get):
        mock_task_get.return_value = mock.Mock(spec=Task)
        mock_user_get.side_effect = User.DoesNotExist
        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.assign_task_to_user(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "User not found"})

    @mock.patch('apps.tasks.models.Task.objects.get')
    @mock.patch('apps.tasks.models.User.objects.get')
    def test_assign_task_already_assigned(self, mock_user_get, mock_task_get):
        mock_task = mock.Mock(spec=Task)
        mock_user_get.return_value = mock.Mock(spec=User)
        mock_task.owner = mock_user_get.return_value
        mock_task_get.return_value = mock_task
        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.assign_task_to_user(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "Task is already assigned to this user"})


    def test_complete_task(self):
        response = self.client.post('/tasks/complete_task', {'task_id': self.task.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_complete_task_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.complete_task(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task not found"})
    def test_delete_task(self):
        response = self.client.delete('/tasks/delete_task', {'task_id': self.task.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_delete_task_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TaskViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.delete_task(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task not found"})


class CommentTestCase(TestCase):
    fixtures = ["tasks"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(email='user1@email.com')
        self.task = Task.objects.create(title='Test Task', description='Test Description', user=self.user,
                                        owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        text = '12345'
        response = self.client.post('/comments/create_comment', {'task_id': self.task.id, 'text': text})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.last()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.text, text)

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_create_comment_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = CommentViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.create_comment(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task not found"})

    @mock.patch('apps.tasks.models.Task.objects.get')
    @mock.patch('apps.tasks.models.Comment.objects.create')
    @mock.patch('apps.tasks.views.send_task_assignment_notification')
    def test_create_comment_send_notification(self, mock_send_notification, mock_comment_create, mock_task_get):
        mock_task = mock.Mock(spec=Task)
        mock_task.status = 'done'
        mock_task.title = "Mock Task Title"
        mock_task_get.return_value = mock_task
        mock_comment = mock.Mock(spec=Comment)
        mock_comment.id = 1
        mock_comment_create.return_value = mock_comment
        view = CommentViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "text": "Test Comment"}
        request.user = mock.Mock()
        response = view.create_comment(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(mock_task.status == 'done')
        self.assertTrue(mock_send_notification.called)
        mock_send_notification.assert_called_once_with(mock_task, 'New Comment to your completed task',
                                                       f'Comment was added to "{mock_task.title}".')

    def test_task_comments(self):
        response = self.client.get(f'/comments/task_comments/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comments = Comment.objects.filter(task=self.task.id)
        serializer = AllCommentSerializer(comments, many=True)
        self.assertEqual(response.data, serializer.data)

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_task_comments_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = CommentViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "user_id": 2}
        request.user = mock.Mock()
        response = view.task_comments(request, task_id=request.data["task_id"])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task was not found"})

    @mock.patch('apps.tasks.views.Task.objects')
    def test_task_comments_forbidden(self, mock_task_objects):
        mock_task = mock.Mock()
        mock_task_objects.get.return_value = mock_task
        mock_task.user = mock.Mock()
        mock_task.owner = mock.Mock()
        view = CommentViewSet()
        request = mock.Mock()
        request.data = {"id": 18}
        request.user = mock.Mock()
        response = view.task_comments(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"error": "You do not have permission to view this task."})


class TimerTestCase(TestCase):
    fixtures = ["tasks"]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(email='user1@email.com')
        self.task = Task.objects.create(title='Test Task', description='Test Description', user=self.user,
                                        owner=self.user)
        self.client.force_authenticate(user=self.user)

    def test_start_timer(self):
        response = self.client.post(f'/timer/start_timer/{self.task.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_start_timer_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TimerViewSet()
        request = mock.Mock()
        request.data = {"id": 1}
        request.user = mock.Mock()
        response = view.start_timer(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task was not found"})

    @mock.patch('apps.tasks.models.Task.objects.get')
    @mock.patch('apps.tasks.models.TimeLog.objects.get')
    def test_start_timer_timer_already_running(self, mock_timelog_get, mock_task_get):
        mock_existing_timelog = mock.Mock(spec=TimeLog)
        mock_existing_timelog.end_time = None
        mock_timelog_get.return_value = mock_existing_timelog
        real_task = Task.objects.create()
        mock_task_get.return_value = real_task
        view = TimerViewSet()
        request = mock.Mock()
        request.data = {"id": real_task.id}
        request.user = mock.Mock()
        response = view.start_timer(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "A timer is already running for this task"})

    def test_stop_timer(self):
        time_log = TimeLog.objects.create(task=self.task, start_time=timezone.now())
        response = self.client.post(f'/timer/stop_timer/{self.task.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        time_log.refresh_from_db()
        self.assertIsNotNone(time_log.end_time)

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_stop_timer_exception_task(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TimerViewSet()
        request = mock.Mock()
        request.data = {"id": 1}
        request.user = mock.Mock()
        response = view.stop_timer(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task was not found"})

    @mock.patch('apps.tasks.models.Task.objects.get')
    @mock.patch('apps.tasks.models.TimeLog.objects.get')
    def test_stop_timer_exception_timelog(self, mock_timelog_get, mock_task_get):
        mock_timelog_get.side_effect = TimeLog.DoesNotExist
        view = TimerViewSet()
        request = mock.Mock()
        real_task = Task.objects.create()
        mock_task_get.return_value = real_task
        request = mock.Mock()
        request.data = {"id": real_task.id}
        request.user = mock.Mock()
        response = view.stop_timer(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Timer not started for this task"})

    def test_add_time_log_manually(self):
        data = {
            'task_id': self.task.id,
            'date': '2023-08-22',
            'duration_minutes': 60,
        }
        response = self.client.post('/timer/add_time_log_manually/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        timer = TimeLog.objects.last()
        self.assertEqual(self.task.id, timer.task.id)

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_add_time_log_manually_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TimerViewSet()
        request = mock.Mock()
        request.data = {"id": 1}
        request.user = mock.Mock()
        response = view.add_time_log_manually(request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task was not found"})

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_search_task_by_title_exception(self, mock_task_get):
        mock_task = mock.Mock(spec=Task)
        mock_task_get.return_value = mock_task
        view = TimerViewSet()
        request = mock.Mock()
        request.data = {"task_id": 1, "date": "invalid_date_format", "duration_minutes": 30}
        request.user = mock.Mock()
        response = view.add_time_log_manually(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Invalid date format"})

    def test_get_time_logs(self):
        response = self.client.get(f'/timer/get_time_logs/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        time_logs = TimeLog.objects.filter(task=self.task)
        serialized = TimeLogSerializer(time_logs, many=True)
        self.assertEqual(response.data, serialized.data)

    @mock.patch('apps.tasks.models.Task.objects.get')
    def test_get_time_logs_exception(self, mock_task_get):
        mock_task_get.side_effect = Task.DoesNotExist
        view = TimerViewSet()
        request = mock.Mock()
        request.data = {"id": 1}
        request.user = mock.Mock()
        response = view.get_time_logs(request, task_id=request.data["id"])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Task was not found"})

    def test_get_time_logged_last_month(self):
        today = timezone.now()
        last_month_start = today - relativedelta(months=1)
        TimeLog.objects.create(task=self.task, start_time=last_month_start, end_time=today, duration_minutes=60)
        response = self.client.get('/timer/get_time_logged_last_month/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["Total time logged last month in minutes"], 60)

    def test_get_top_20_tasks_last_month(self):
        today = timezone.now()
        last_month_start = today - relativedelta(days=20)
        for i in range(10):
            task = Task.objects.create(title=f'Test Task {i}', description='Test Description', user=self.user,
                                       owner=self.user)
            TimeLog.objects.create(task=task, start_time=last_month_start, end_time=today, duration_minutes=60)
        response = self.client.get('/timer/get_top_20_tasks_last_month/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

        for i in range(10, 20):
            task = Task.objects.create(title=f'Test Task {i}', description='Test Description', user=self.user,
                                       owner=self.user)
            TimeLog.objects.create(task=task, start_time=last_month_start, end_time=today, duration_minutes=120 + i)
        response = self.client.get('/timer/get_top_20_tasks_last_month/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 20)
        self.assertEqual(response.data[0]['total_time'], 139)

