from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Subquery, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


from apps.common.helpers import send_notification
from apps.tasks.models import Task, Comment, TimeLog
from apps.tasks.serializers import TaskSerializer, TaskListSerializer, ShortTaskSerializer, \
    CreateCommentSerializer, AllCommentSerializer, TaskAssignSerializer, CreateTimeLogSerializer,\
    TimeLogSerializer, StopTimeLogSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('id')
    serializer_class = TaskSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ShortTaskSerializer
        if self.action == "comments":
            return AllCommentSerializer
        if self.action in ["list", "get_top_20_tasks_last_month", "my", "created", "completed"]:
            return TaskListSerializer
        if self.action == "assign":
            return TaskAssignSerializer
        if self.action == "time_logs_by_id":
            return TimeLogSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "created":
            queryset = queryset.annotate(total_duration=Subquery(TimeLog.objects.filter(task=OuterRef('id')).values(
                'task').annotate(total=Sum('duration')).values('total'))).filter(user=self.request.user)
        if self.action == "my":
            queryset = queryset.annotate(total_duration=Subquery(TimeLog.objects.filter(task=OuterRef('id')).values(
                'task').annotate(total=Sum('duration')).values('total'))).filter(owner=self.request.user)
        if self.action == "completed":
            queryset = queryset.annotate(total_duration=Subquery(TimeLog.objects.filter(task=OuterRef('id')).values(
                'task').annotate(total=Sum('duration')).values('total'))).filter(status=Task.Status.DONE)
        if self.action == "comments":
            queryset = queryset.filter(task=self.kwargs.get("pk"))
        if self.action == "list":
            queryset = queryset.annotate(total_duration=Subquery(TimeLog.objects.filter(task=OuterRef('id')).values(
                'task').annotate(total=Sum('duration')).values('total')))
        if self.action == "get_top_20_tasks_last_month":
            queryset = Task.objects.filter(
                owner=self.request.user,
                timelogs__start_time__gte=timezone.now() - relativedelta(months=1),
                timelogs__start_time__lte=timezone.now(),
            ).annotate(total_duration=Sum('timelogs__duration'))
        if self.action == "time_logs_by_id":
            queryset = queryset.filter(task=self.kwargs.get("pk"))
        return queryset.order_by('id')

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
        serializer = self.get_serializer(data=request.data)
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

    @action(methods=['get'], detail=True, url_path="time_logs_by_id", queryset=TimeLog.objects.all())
    def time_logs_by_id(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path="top-20-tasks")
    def get_top_20_tasks_last_month(self, request):
        top_tasks = self.get_queryset().order_by("-total_duration")[:20]
        serializer = self.get_serializer(top_tasks, many=True).data
        return Response(serializer, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = AllCommentSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCommentSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        task_id = self.request.data['task']
        task = get_object_or_404(Task, id=task_id)
        send_notification([task.owner.email], "New comment!", "You task was commented")


class TimerViewSet(viewsets.ModelViewSet):
    queryset = TimeLog.objects.all()
    serializer_class = CreateTimeLogSerializer

    def get_serializer_class(self):
        if self.action == "add_time_log_manually":
            return TimeLogSerializer
        if self.action == "stop":
            return StopTimeLogSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "get_time_logged_last_month":
            queryset = TimeLog.objects.filter(
                task__owner=self.request.user,
                start_time__gte=timezone.now() - relativedelta(months=1),
                start_time__lte=timezone.now(),
                user=self.request.user,
            ).aggregate(total=Sum('duration')).get('total')

        return queryset

    def perform_create(self, serializer):
        task = serializer.validated_data['task']
        task.status = Task.Status.IN_PROGRESS
        task.save()
        serializer.save(user=self.request.user)

    @action(methods=['post'], detail=False, url_path="stop")
    def stop(self, request):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Timer was stopped successfully"})

    @action(methods=['post'], detail=False, url_path="manually")
    def add_time_log_manually(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=False, serializer_class=None, url_path="time-logged-last-month")
    def get_time_logged_last_month(self, request):
        total_time_logged = self.get_queryset()
        return Response({"total_time_logged": total_time_logged or 0})
