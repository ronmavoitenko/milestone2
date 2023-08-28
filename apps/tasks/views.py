from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.helpers import send_notification
from apps.tasks.models import Task, Comment, TimeLog
from apps.tasks.serializers import TaskSerializer, TaskListSerializer, ShortTaskSerializer, \
    CreateCommentSerializer, AllCommentSerializer, TimeLogSerializer, CreateTimeLogSerializer, TaskAssignSerializer


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ShortTaskSerializer
        if self.action == "create":
            return TaskSerializer
        if self.action == "comments":
            return AllCommentSerializer

        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "created":
            queryset = queryset.filter(user=self.request.user)
        if self.action == "my":
            queryset = queryset.filter(owner=self.request.user)
        if self.action == "completed":
            queryset = queryset.filter(status=Task.Status.DONE)
        if self.action == "comments":
            queryset = queryset.filter(task=self.kwargs.get("pk"))

        return queryset

    @action(methods=['get'], detail=False, serializer_class=TaskListSerializer, url_path="created-tasks")
    def created(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(methods=['get'], detail=False, serializer_class=TaskListSerializer, url_path="my-tasks")
    def my(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(methods=['get'], detail=False, serializer_class=TaskListSerializer, url_path="completed-tasks")
    def completed(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(request_body=no_body)
    @action(methods=['patch'], detail=True, url_path="complete")
    def complete(self, request, *args, **kwargs):
        task = self.get_object()
        task.status = Task.Status.DONE
        task.save()
        send_notification(task.owner.email, "New commented task was complete!", "New task was assigned to You")
        return Response({"success": True}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, owner=self.request.user)

    @action(methods=['post'], detail=True, serializer_class=TaskAssignSerializer, url_path="assign")
    def assign(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = TaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        task.owner = user
        task.save()
        send_notification([task.owner.email], "New task!", "New task was assigned to You")
        return Response({"success": True, 'message': f'Task {task.title} assigned to user {user.get_full_name()}'})

    @action(methods=['get'], detail=True, serializer_class=AllCommentSerializer, url_path="comments",
            queryset=Comment.objects.all(), search_fields=None)
    def comments(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = AllCommentSerializer
    filter_backends = [filters.SearchFilter]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCommentSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        task_id = self.request.data['task']
        task = get_object_or_404(Task, id=task_id)
        send_notification([task.owner.email], "New comment!", "You task was commented")
