from rest_framework.routers import DefaultRouter
from apps.tasks.views import TaskViewSet, CommentViewSet, TimerViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'tasks', TaskViewSet, basename='task'),
router.register(r'comments', CommentViewSet, basename='comments'),
router.register(r'timer', TimerViewSet, basename='timer'),

urlpatterns = router.urls
