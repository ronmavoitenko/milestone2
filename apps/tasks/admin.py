from django.contrib import admin
from apps.tasks.models import Task, Comment

# Register your models here

admin.site.register(Task)
admin.site.register(Comment)