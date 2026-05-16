# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'
urlpatterns = [
    path('', views.task_list, name='list'),
    path('task/<int:task_id>/', views.task_detail, name='detail'),
    path('task/add/', views.task_add, name='add'),
    path('task/<int:task_id>/edit/', views.task_edit, name='edit'),
    path('task/<int:task_id>/delete/', views.task_delete, name='delete'),
    path('task/<int:task_id>/image/<path:filename>', views.serve_task_image, name='task_image'),
    path('attempt/<int:attempt_id>/results/', views.get_attempt_results, name='attempt_results'),
    path('api/check/', views.check_solution, name='check'),
    path('api/task/<int:task_id>/', views.get_task_info, name='info'),

    path('task/<int:task_id>/sample/', views.sample_solution, name='sample_solution'),
]
