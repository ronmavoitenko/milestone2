from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from .models import Task, Comment
from .serializers import SerializerTask, TaskListSerializer, TaskDetailsByIdSerializer, \
    CreateCommentSerializer, AllCommentSerializer

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
            return Response({"error": "There no tasks with this title"}, status=status.HTTP_404_NOT_FOUND)

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
        tasks = Task.objects.filter(status='done', user=request.user)
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
            return Response({'error': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
