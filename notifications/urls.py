from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('api/', views.get_notifications, name='api'),
    path('api/<int:notification_id>/read/', views.mark_as_read, name='mark_read'),
    path('api/read-all/', views.mark_all_as_read, name='mark_all_read'),
]