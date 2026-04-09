# tasks/urls.py
from django.urls import path
from . import views


app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('api/task/<int:task_id>/', views.get_task_info, name='task_info'),  # API для AJAX
    path('task/add/', views.task_add, name='task_add'),
    # path('api/structure/', views.get_structure, name='get_structure'),
    path('task/<int:task_id>/image/<path:filename>', views.serve_task_image, name='task_image'),
    path('attempt/<int:attempt_id>/results/', views.get_attempt_results, name='attempt_results'),

    path('task/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:task_id>/delete/', views.task_delete, name='task_delete'),


    # Подборки задач
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/create/', views.collection_create, name='collection_create'),
    path('collections/<int:collection_id>/edit/', views.collection_edit, name='collection_edit'),
    path('collections/<int:collection_id>/', views.collection_detail, name='collection_detail'),
    path('collections/<int:collection_id>/start/', views.start_collection, name='start_collection'),
    path('attempt/<int:attempt_id>/', views.collection_attempt, name='collection_attempt'),


# Выдача КР
    path('collections/<int:collection_id>/assign/', views.assign_collection, name='assign_collection'),
    path('my-assignments/', views.my_assignments, name='my_assignments'),
    path('collection/<int:attempt_id>/complete/', views.complete_collection, name='complete_collection'),
    path('check-solution/', views.check_solution, name='check_solution'),
]
