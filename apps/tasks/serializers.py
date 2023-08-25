from django.db.models import Sum
from rest_framework import serializers
from .models import Task, Comment, TimeLog


class SerializerTask(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("title", "description")

    def create(self, validated_data):
        task = Task.objects.create(**validated_data)
        task.user = self.context['request'].user
        task.owner = self.context['request'].user
        return task


class TaskListSerializer(serializers.ModelSerializer):
    total_time_minutes = serializers.SerializerMethodField()

    def get_total_time_minutes(self, task):
        total_time = task.timelog_set.aggregate(total=Sum('duration')).get('total')
        return total_time or 0

    class Meta:
        model = Task
        fields = ("id", "title", "total_time_minutes")


class AssignTask(serializers.ModelSerializer):
    user_id = serializers.IntegerField()

    class Meta:
        model = Task
        fields = ('user_id',)


class TaskDetailsByIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "description", "status", "owner")


class CreateCommentSerializer(serializers.ModelSerializer):
    task_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ("task_id", "text")


class AllCommentSerializer(serializers.ModelSerializer):
    task = serializers.CharField()

    class Meta:
        model = Comment
        fields = ("id", "task", "user", "text")


class TimeLogSerializer(serializers.ModelSerializer):
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M", allow_null=True)

    class Meta:
        model = TimeLog
        fields = ("task", "start_time", "end_time", "duration")
