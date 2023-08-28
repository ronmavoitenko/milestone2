from django.contrib.auth.models import User
from django.db.models import Sum
from rest_framework import serializers
from .models import Task, Comment, TimeLog


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("title", "description")


class TaskListSerializer(serializers.ModelSerializer):
    total_duration = serializers.SerializerMethodField()

    def get_total_duration(self, task):
        total_time = task.timelogs.aggregate(total=Sum('duration')).get('total')
        return total_time or 0

    class Meta:
        model = Task
        fields = ("id", "title", "total_duration")


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
    class Meta:
        model = TimeLog
        fields = ("task",)
