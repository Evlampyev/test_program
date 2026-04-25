# shared/__init__.py
from .models import ClassStructure, TaskPlacement
from .utils import get_task_files
from .decorators import is_teacher

__all__ = [
    'ClassStructure', 'TaskPlacement',
    'get_task_files',
    'is_teacher',
]
