# tasks/__init__.py
from .models import Task, DifficultyLevel, TaskAttempt, UploadedProgram
from .views import task_list, task_detail, task_add, task_edit, task_delete, check_solution

__all__ = [
    'Task', 'DifficultyLevel', 'TaskAttempt', 'UploadedProgram',
    'task_list', 'task_detail', 'task_add', 'task_edit', 'task_delete', 'check_solution',
]