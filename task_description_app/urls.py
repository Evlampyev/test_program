# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('api/task/<int:task_id>/', views.get_task_info, name='task_info'),  # API для AJAX
    path('task/add/', views.task_add, name='task_add'),
    path('api/structure/', views.get_structure, name='get_structure'),
]
