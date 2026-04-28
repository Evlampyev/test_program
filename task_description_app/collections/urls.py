# collections/urls.py
from django.urls import path
from . import views

app_name = 'collections'

urlpatterns = [
    # Подборки задач
    path('', views.collection_list, name='list'),
    path('create/', views.collection_create, name='create'),
    path('<int:collection_id>/edit/', views.collection_edit, name='edit'),
    path('<int:collection_id>/', views.collection_detail, name='detail'),
    path('<int:collection_id>/start/', views.start_collection, name='start'),
    path('collection/<int:collection_id>/delete/', views.collection_delete, name='delete'),
    path('attempt/<int:attempt_id>/', views.collection_attempt, name='attempt'),

    # Выдача КР
    path('<int:collection_id>/assign/', views.assign_collection, name='assign'),
    path('collection/<int:attempt_id>/complete/', views.complete_collection, name='complete'),
    path('my-assignments/', views.my_assignments, name='my_assignments'),
    # path('check-solution/', views.check_solution, name='check_solution'),
    path('api/collection/<int:collection_id>/request-time/', views.student_request_time_extension,
         name='student_request_time'),
]
