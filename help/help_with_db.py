from django.db import connection
from django.db.models.deletion import Collector
from task_description_app.models import Task

obj = Task.objects.get(pk=...)  # или DifficultyLevel
collector = Collector(using='default')
collector.collect([obj])
print(collector.data)
