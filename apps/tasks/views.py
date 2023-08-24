from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from apps.tasks.models import Task, Comment, TimeLog
from apps.tasks.serializers import SerializerTask, TaskListSerializer, TaskDetailsByIdSerializer, \
    CreateCommentSerializer, AllCommentSerializer, TimeLogSerializer


def send_task_assignment_notification(task, subject, message):
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [task.owner.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=True)


class TaskViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'description'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    def create_task(self, request):
        serializer = SerializerTask(data=request.data, context={'request': request})
        if serializer.is_valid():
            task = serializer.save(user=request.user, owner=request.user)
            return Response({"id": task.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def created_tasks(self, request):
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    def search_task_by_title(self, request):
        title = request.data.get("title")
        try:
            created_tasks = Task.objects.filter(title__icontains=title, user=request.user)
            assigned_tasks = Task.objects.filter(title__icontains=title, owner=request.user)
            tasks = created_tasks | assigned_tasks
        except Task.DoesNotExist:
            return Response({"error": "There are no tasks with this title"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def task_details_by_id(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            if task.user == request.user or task.owner == request.user:
                serializer = TaskDetailsByIdSerializer(task)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "You do not have permission to view this task."},
                                status=status.HTTP_403_FORBIDDEN)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    def my_tasks(self, request):
        tasks = Task.objects.filter(owner=request.user)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def completed_tasks(self, request):
        created_tasks = Task.objects.filter(status='done', user=request.user)
        assigned_tasks = Task.objects.filter(status='done', owner=request.user)
        tasks = created_tasks | assigned_tasks
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id', 'user_id'],
            properties={
                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )
    )
    def assign_task_to_user(self, request):
        task_id = request.data.get("task_id")
        user_id = request.data.get("user_id")
        try:
            task = Task.objects.get(id=task_id, user=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            new_owner = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        subject = 'New Task Assignment'
        message = f'A new task "{task.title}" has been assigned to you.'
        if task.owner != new_owner:
            task.owner = new_owner
            task.save()
            send_task_assignment_notification(task, subject, message)
            return Response({"message": "Task assigned successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Task is already assigned to this user"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id'],
            properties={
                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )
    )
    def complete_task(self, request):
        task_id = request.data.get("task_id")
        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        task.status = 'done'
        task.save()
        return Response({"message": "Task completed successfully"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id'],
            properties={
                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )
    )
    def delete_task(self, request):
        task_id = request.data.get("task_id")
        try:
            task = Task.objects.get(id=task_id, user=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        task.delete()
        return Response({"message": "Task deleted successfully"}, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id', 'text'],
            properties={
                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'text': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def create_comment(self, request):
        task_id = request.data.get('task_id')
        text = request.data.get('text')
        try:
            task = Task.objects.get(id=task_id, user=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        comment = Comment.objects.create(task=task, text=text, user=request.user)
        if task.status == 'done':
            subject = 'New Comment to your completed task'
            message = f'Comment was added to "{task.title}".'
            send_task_assignment_notification(task, subject, message)
        else:
            subject = 'New Comment to your task'
            message = f'Comment was added to "{task.title}".'
            send_task_assignment_notification(task, subject, message)
        serializer = CreateCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def task_comments(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            if task.user == request.user or task.owner == request.user:
                comments = Comment.objects.filter(task=task)
                serializer = AllCommentSerializer(comments, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to view this task.'},
                                status=status.HTTP_403_FORBIDDEN)
        except Task.DoesNotExist:
            return Response({'error': 'Task was not found'}, status=status.HTTP_404_NOT_FOUND)


class TimerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def start_timer(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task was not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            TimeLog.objects.get(task=task, end_time__isnull=True)
            return Response({"error": "A timer is already running for this task"}, status=status.HTTP_400_BAD_REQUEST)
        except TimeLog.DoesNotExist:
            pass

        TimeLog.objects.create(task=task, start_time=timezone.now())
        task.status = 'in_progress'
        task.save()

        return Response({"message": "Timer started successfully"}, status=status.HTTP_200_OK)

    def stop_timer(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task was not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            time_log = TimeLog.objects.get(task=task, end_time__isnull=True)
        except TimeLog.DoesNotExist:
            return Response({"error": "Timer not started for this task"}, status=status.HTTP_400_BAD_REQUEST)

        time_log.end_time = timezone.now()
        time_log.duration_minutes = (time_log.end_time - time_log.start_time).seconds // 60
        time_log.save()

        return Response({"message": f"Timer stopped successfully, you worked on this task {time_log.duration_minutes} minutes"},
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['task_id', 'date', 'duration_minutes'],
            properties={
                'task_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'date': openapi.Schema(type=openapi.TYPE_STRING, example="yyyy-mm-dd"),
                'duration_minutes': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
    )
    def add_time_log_manually(self, request):
        task_id = request.data.get('task_id')
        date_str = request.data.get('date')
        duration_minutes = request.data.get('duration_minutes')

        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task was not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        start_time=timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        TimeLog.objects.create(task=task, start_time=start_time, end_time=start_time, duration_minutes=duration_minutes)

        return Response({"message": "Time log added successfully"}, status=status.HTTP_201_CREATED)

    def get_time_logs(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id, owner=request.user)
        except Task.DoesNotExist:
            return Response({"error": "Task was not found"}, status=status.HTTP_404_NOT_FOUND)

        time_logs = TimeLog.objects.filter(task=task)
        serializer = TimeLogSerializer(time_logs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_time_logged_last_month(self, request):
        today = timezone.now()
        last_month_start = today - relativedelta(months=1)

        total_time_logged = TimeLog.objects.filter(
            task__owner=request.user,
            start_time__gte=last_month_start,
            start_time__lte=today,
        ).aggregate(total=Sum('duration_minutes')).get('total')

        return Response({"Total time logged last month in minutes": total_time_logged or 0}, status=status.HTTP_200_OK)

    def get_top_20_tasks_last_month(self, request):
        today = timezone.now()
        last_month_start = today - relativedelta(months=1)

        top_tasks = Task.objects.filter(
            owner=request.user,
            timelog__start_time__gte=last_month_start,
            timelog__start_time__lte=today,
        ).annotate(total_time=Sum('timelog__duration_minutes')).order_by('-total_time')[:20]

        serializes_tasks = [
            {
                "id": task.id,
                "title": task.title,
                "total_time": task.total_time or 0
            }
            for task in top_tasks
        ]

        return Response(serializes_tasks, status=status.HTTP_200_OK)
