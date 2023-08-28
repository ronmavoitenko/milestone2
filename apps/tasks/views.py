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


class TimerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = TimeLog.objects.all()
    serializer_class = TimeLogSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateTimeLogSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        task_id = self.request.data['task']
        task = Task.objects.get(pk=task_id)
        try:
            TimeLog.objects.get(task=task, end_time__isnull=True)
            return Response({"error": "A timer is already running for this task"}, status=status.HTTP_400_BAD_REQUEST)
        except TimeLog.DoesNotExist:
            pass

        TimeLog.objects.create(task=task, start_time=timezone.now())
        task.status = Task.Status.IN_PROGRESS
        task.save()

    @swagger_auto_schema(request_body=no_body)
    @action(methods=['post'], detail=True, url_path="stop")
    def stop(self, request, pk=None):
        task = Task.objects.get(pk=pk)
        time_log = TimeLog.objects.get(task=task, end_time__isnull=True)
        time_log.end_time = timezone.now()
        time_log.duration = (time_log.end_time - time_log.start_time).seconds // 60
        time_log.save()
    # def stop_timer(self, request, task_id):
    #     try:
    #         task = Task.objects.get(id=task_id, owner=request.user)
    #     except Task.DoesNotExist:
    #         return Response({"error": "Task was not found"}, status=status.HTTP_404_NOT_FOUND)
    #
    #     try:
    #         time_log = TimeLog.objects.get(task=task, end_time__isnull=True)
    #     except TimeLog.DoesNotExist:
    #         return Response({"error": "Timer not started for this task"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     time_log.end_time = timezone.now()
    #     time_log.duration_minutes = (time_log.end_time - time_log.start_time).seconds // 60
    #     time_log.save()
    #
    #     return Response(
    #         {"message": f"Timer stopped successfully, you worked on this task {time_log.duration_minutes} minutes"},
    #         status=status.HTTP_200_OK)


"""
class TimerViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]


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
        return Response(serializes_tasks, status=status.HTTP_200_OK)"""
