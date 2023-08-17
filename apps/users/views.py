from django.contrib.auth.models import User
from drf_util.decorators import serialize_decorator
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.views import APIView

from .serializers import UserSerializer, UserListSerializer


# Create your views here.


class RegisterUserView(GenericAPIView):
    serializer_class = UserSerializer

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @serialize_decorator(UserSerializer)
    def post(self, request):
        validated_data = request.serializer.validated_data

        # Get password from validated data
        password = validated_data.pop("password")

        user = self.serializer_class().create_user(validated_data, password)

        # Set password
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


class UsersListView(APIView):
    serializer_class = UserListSerializer

    def get(self, request):
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
