from rest_framework import filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.generics import get_object_or_404

from apps.tasks.models import Task, Comment, TimeLog
from apps.tasks.serializers import SerializerTask, TaskListSerializer, TaskDetailsByIdSerializer, AssignTask, \
    CreateCommentSerializer, AllCommentSerializer, TimeLogSerializer


def send_task_assignment_notification(task, subject, message):
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [task.owner.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=True)


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = SerializerTask
    filter_backends = [filters.SearchFilter]
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TaskDetailsByIdSerializer
        if self.action == "create":
            return SerializerTask
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "created":
            queryset = queryset.filter(user=self.request.user)
        if self.action == "my":
            queryset = queryset.filter(owner=self.request.user)
        if self.action == "completed":
            queryset = queryset.filter(status=Task.Status.DONE)

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

    @action(methods=['patch'], detail=True, serializer_class=None, url_path="complete-task")
    def complete(self, request, *args, **kwargs):
        task = self.get_object()
        task.status = Task.Status.DONE
        task.save()
        return Response({"success": True}, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, owner=self.request.user)

    @action(methods=['post'], detail=True, serializer_class=AssignTask, url_path="assign-task")
    def assign(self, request, pk=None):
        task = self.get_object()
        serializer = AssignTask(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        user = get_object_or_404(User, id=user_id)
        task.owner = user
        task.save()
        return Response({'message': f'Task {task.id} assigned to user {user_id}'})


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = AllCommentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["task__id"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCommentSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
