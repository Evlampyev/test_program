# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('api/task/<int:task_id>/', views.get_task_info, name='task_info'),
    path('task/add/', views.task_add, name='task_add'),
    # path('get-topics/', views.get_topics, name='get_topics'),
    # path('get-lessons/', views.get_lessons, name='get_lessons'),
    # path('get-levels/', views.get_levels, name='get_levels'),
    # path('get-existing-tasks/', views.get_existing_tasks, name='get_existing_tasks'),
]
