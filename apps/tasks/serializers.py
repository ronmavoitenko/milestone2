from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from apps.tasks.models import Task, Comment, TimeLog


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "description")


class TaskListSerializer(serializers.ModelSerializer):
    total_duration = serializers.IntegerField()

    class Meta:
        model = Task
        fields = ("id", "title", "description", "total_duration")


class TaskAssignSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())


class ShortTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "description", "status", "owner")


class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("task", "text")


class AllCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "task", "user", "text")


class TimeLogSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M", allow_null=True)

    class Meta:
        model = TimeLog
        fields = ("task", "start_time", "end_time", "duration")


class CreateTimeLogSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = TimeLog
        fields = ("task",)

    def validate_task(self, value):
        if TimeLog.objects.filter(task=value, end_time__isnull=True).exists():
            raise serializers.ValidationError("A timer is already running for this task")
        return value


class StopTimeLogSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = TimeLog
        fields = ("task",)

    def validate_task(self, value):
        active_timer = TimeLog.objects.filter(task=value, end_time__isnull=True)
        if not active_timer.exists():
            raise serializers.ValidationError("No running timer found for this task")
        return value

    def save(self, **kwargs):
        task = self.validated_data['task']
        time_log = TimeLog.objects.get(task=task, end_time__isnull=True)
        time_log.end_time = timezone.now()
        time_log.duration = (time_log.end_time - time_log.start_time).seconds // 60
        time_log.save()
