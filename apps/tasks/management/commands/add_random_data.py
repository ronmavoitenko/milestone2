import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from apps.tasks.models import Task, TimeLog


class Command(BaseCommand):
    help = 'Добавляет случайные задачи и записи времени'

    def handle(self, *args, **options):
        Task.objects.all().delete()
        TimeLog.objects.all().delete()

        users = User.objects.all()

        for i in range(25000):
            task_user = random.choice(users)
            task_owner = random.choice(users)
            task = Task.objects.create(
                title=f"Задача {i}",
                description=f"Описание для задачи {i}",
                owner=task_owner,
                user=task_user
            )
            for j in range(2): #random.randint(1, 2)):
                start_time = timezone.now() - timezone.timedelta(days=random.randint(0, 30))
                end_time = start_time + timezone.timedelta(hours=random.randint(1, 10))
                TimeLog.objects.create(
                    task=task,
                    start_time=start_time,
                    end_time=end_time
                )

        self.stdout.write(self.style.SUCCESS('Успешно добавлены случайные данные.'))
