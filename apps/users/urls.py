from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.views import UserViewSet

router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user'),

urlpatterns = [
    path("user/register/", UserViewSet.as_view({'post': 'register'}), name="register"),
    path("user/users_list/", UserViewSet.as_view({'get': 'users_list'}), name="users_list"),
    path("token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
] + router.urls

