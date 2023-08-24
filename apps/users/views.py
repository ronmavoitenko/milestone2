from django.contrib.auth.models import User
from drf_util.decorators import serialize_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, viewsets

from apps.users.serializers import UserSerializer, UserListSerializer


class UserViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['first_name', 'last_name', 'email', 'password'],
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.FORMAT_EMAIL, example="user@example.com"),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    @serialize_decorator(UserSerializer)
    def register(self, request):
        validated_data = request.serializer.validated_data
        password = validated_data.pop("password")

        user = User.objects.create(
            **validated_data,
            username=validated_data['email'],
        )
        user.set_password(password)
        user.save()
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        response_data = {
            'user': user_data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def users_list(self, request):
        users = User.objects.all()
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

