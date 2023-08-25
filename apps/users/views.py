from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from rest_framework import viewsets

from apps.users.serializers import UserSerializer, UserListSerializer


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = UserListSerializer
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        user = serializer.save(username=self.request.data['email'])
        user.set_password(serializer.validated_data['password'])
