# upload_app/urls.py
from django.urls import path
from . import views

app_name = 'upload_app'

urlpatterns = [
    path('', views.upload_python_file, name='upload_file'),
]