# task_description_app/urls.py
from django.urls import path, include

app_name = 'tasks_&_collections'

urlpatterns = [
    path('', include('task_description_app.tasks.urls')),
    path('collections/', include('task_description_app.collections.urls')),
]
