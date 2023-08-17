from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='user', default=1)
    status = models.CharField(max_length=20, choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='todo')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner', default=1)

    def __str__(self):
        return self.title

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userComment')
    text = models.TextField()

    def __str__(self):
        return f"Comment by {self.task.user.username} on {self.task.title}"
