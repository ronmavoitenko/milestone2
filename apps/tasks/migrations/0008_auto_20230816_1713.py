# Generated by Django 3.2.16 on 2023-08-16 14:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tasks', '0007_auto_20230816_1523'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='user_creater',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='user_owner',
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='userComment', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.task'),
        ),
    ]