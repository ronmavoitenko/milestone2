from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
import random
from django.utils import timezone
from apps.tasks.models import Task, TimeLog


class Command(BaseCommand):
    help = 'Creates random tasks and time logs'

    def handle(self, *args, **options):
        Task.objects.all().delete()
        TimeLog.objects.all().delete()

        users = User.objects.all()

        task_list = []
        timelog_list = []
        for i in range(25000):
            task_user = random.choice(users)
            task_owner = random.choice(users)
            task = Task(
                title=f"Задача {i}",
                description=f"Описание для задачи {i}",
                owner=task_owner,
                user=task_user
            )
            task_list.append(task)
            for j in range(2):
                start_time = timezone.now() - timezone.timedelta(days=random.randint(0, 30))
                end_time = start_time + timezone.timedelta(hours=random.randint(1, 10))
                timer_creater = random.choice(users)
                timelog = TimeLog(
                    task=task,
                    start_time=start_time,
                    end_time=end_time,
                    duration=(end_time - start_time).seconds // 60,
                    user=timer_creater
                )
                timelog_list.append(timelog)

        Task.objects.bulk_create(task_list)
        TimeLog.objects.bulk_create(timelog_list)

        self.stdout.write(self.style.SUCCESS('Successfully created random tasks and time logs'))
