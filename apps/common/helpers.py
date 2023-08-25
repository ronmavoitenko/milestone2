from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings

schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version="v1",
        description="Enjoy",
    ),
    public=True,
    permission_classes=[AllowAny],
)


def send_notification(task, subject, message):
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [task.owner.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=True)
