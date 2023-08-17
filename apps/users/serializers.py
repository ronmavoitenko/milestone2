from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "password",
        )

    def create_user(self, validated_data, password):
        user = User.objects.create(
            **validated_data,
            username = validated_data['email'],
        )
        user.set_password(password)
        user.save()
        return user



"""class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)"""


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "full_name")

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"