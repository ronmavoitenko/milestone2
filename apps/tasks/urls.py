from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, CommentViewSet, TimerViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task'),
router.register(r'comments', CommentViewSet, basename='comments'),
router.register(r'timer', TimerViewSet, basename='timer'),

urlpatterns = [
    path('timer/start_timer/<int:task_id>', TimerViewSet.as_view({'post': 'start_timer'}), name='start_timer'),
    path('timer/stop_timer/<int:task_id>', TimerViewSet.as_view({'post': 'stop_timer'}), name='stop_timer'),
    path('timer/add_time_log_manually/', TimerViewSet.as_view({'post': 'add_time_log_manually'}), name='add_time_log_manually'),
    path('timer/get_time_logs/<int:task_id>/', TimerViewSet.as_view({'get': 'get_time_logs'}), name='get_time_logs'),
    path('timer/get_time_logged_last_month/', TimerViewSet.as_view({'get': 'get_time_logged_last_month'}), name='get_time_logged_last_month'),
    path('timer/get_top_20_tasks_last_month/', TimerViewSet.as_view({'get': 'get_top_20_tasks_last_month'}), name='get_top_20_tasks_last_month'),

    path('comments/create_comment', CommentViewSet.as_view({'post': 'create_comment'}), name='create_comment'),
    path('comments/task_comments/<int:task_id>/', CommentViewSet.as_view({'get': 'task_comments'}), name='task_comments'),

    path('tasks/create-task/', TaskViewSet.as_view({'post': 'create_task'}), name='create-task'),
    path('tasks/created_tasks/', TaskViewSet.as_view({'get': 'created_tasks'}), name='created_tasks'),
    path('tasks/search_task_by_title/', TaskViewSet.as_view({'post': 'search_task_by_title'}), name='search_task_by_title'),
    path('tasks/task_details_by_id/<int:task_id>/', TaskViewSet.as_view({'get': 'task_details_by_id'}), name='task_details_by_id'),
    path('tasks/my_tasks', TaskViewSet.as_view({'get': 'my_tasks'}), name='my_tasks'),
    path('tasks/completed_tasks', TaskViewSet.as_view({'get': 'completed_tasks'}), name='completed_tasks'),
    path('tasks/assign_task_to_user', TaskViewSet.as_view({'post': 'assign_task_to_user'}), name='assign_task_to_user'),
    path('tasks/complete_task', TaskViewSet.as_view({'post': 'complete_task'}), name='complete_task'),
    path('tasks/delete_task', TaskViewSet.as_view({'delete': 'delete_task'}), name='delete_task'),
] + router.urls
