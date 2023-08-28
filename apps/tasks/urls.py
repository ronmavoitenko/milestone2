from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, CommentViewSet, TimerViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'tasks', TaskViewSet, basename='task'),
router.register(r'comments', CommentViewSet, basename='comments'),
router.register(r'timer', TimerViewSet, basename='timer'),

urlpatterns = router.urls
