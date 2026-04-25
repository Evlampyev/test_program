# views.py (приложение tasks)
import os
import re

from django.conf import settings

import markdown
from . import ClassStructure, TaskPlacement


def get_task_path_from_structure(task):
    """Получает путь к задаче из структуры ClassStructure"""
    placements = TaskPlacement.objects.filter(task=task).select_related('structure_node')
    if not placements.exists():
        return None

    # Берем первый placement (или можно объединить несколько)
    placement = placements.first()
    node = placement.structure_node

    # Собираем путь из названий узлов
    path_parts = []
    current = node
    while current:
        path_parts.insert(0, current.name)
        current = current.parent

    # Добавляем папку задачи
    path_parts.append(f"task_{task.id}")

    return os.path.join(settings.BASE_DIR, 'tasks_for_tests', *path_parts)


def get_or_create_structure_node(class_name, topic_name, lesson_name, level_name):
    """Получает или создает узлы структуры"""
    # Уровень 0: Класс
    class_node, _ = ClassStructure.objects.get_or_create(
        name=class_name,
        level=0,
        parent=None
    )

    # Уровень 1: Тема
    topic_node, _ = ClassStructure.objects.get_or_create(
        name=topic_name,
        level=1,
        parent=class_node
    )

    # Уровень 2: Урок
    lesson_node, _ = ClassStructure.objects.get_or_create(
        name=lesson_name,
        level=2,
        parent=topic_node
    )

    # Уровень 3: Уровень сложности
    level_node, _ = ClassStructure.objects.get_or_create(
        name=level_name,
        level=3,
        parent=lesson_node
    )

    return level_node
