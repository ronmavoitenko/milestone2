from rest_framework import serializers
from .models import Task, Comment

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
    class Meta:
        model = Task
        fields = ("id", "title")


class TaskDetailsByIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ("id", "title", "description", "status", "owner")

class CreateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields =  ("id",)

class AllCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "task", "user", "text")