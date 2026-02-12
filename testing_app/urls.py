# testing_app/urls.py
from django.urls import path
from . import views

app_name = 'testing_app'

urlpatterns = [
    path('run-tests/<int:program_id>/', views.run_tests, name='run_tests'),
]