from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterUserView, UsersListView

urlpatterns = [
    path("usersList", UsersListView.as_view(), name="all_users"),
    path("register", RegisterUserView.as_view(), name="token_register"),
    path("token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
]

