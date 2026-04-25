# task_description_app/__init__.py
# Экспортируем основные модели для удобства импорта
from .tasks.models import Task, DifficultyLevel, TaskAttempt, UploadedProgram
from .collections.models import Collection, CollectionItem, CollectionAttempt, CollectionAssignment
from .shared.models import ClassStructure, TaskPlacement

__all__ = [
    'Task', 'DifficultyLevel', 'TaskAttempt', 'UploadedProgram',
    'Collection', 'CollectionItem', 'CollectionAttempt', 'CollectionAssignment',
    'ClassStructure', 'TaskPlacement',
]