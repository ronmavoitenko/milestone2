from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo"
        IN_PROGRESS = "in_progress"
        DONE = "done"
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks', null=True)


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()


class TimeLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(default=0)
