# shared/models.py
from django.db import models
from django.contrib.auth import get_user_model

from task_description_app.tasks import Task

User = get_user_model()


class ClassStructure(models.Model):
    """Структура классов/тем/уроков (только для навигации)"""
    name = models.CharField('Название', max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField('Уровень вложенности', default=0)  # 0-класс, 1-тема, 2-урок, 3-уровень
    order = models.IntegerField('Порядок', default=0)

    class Meta:
        db_table = 'task_description_app_classstructure'
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['level']),
            models.Index(fields=['order']),
        ]
        ordering = ['level', 'order', 'name']  # сортировка по умолчанию

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Возвращает полный путь в виде списка"""
        path = []
        current = self
        while current:
            path.append(current.name)
            current = current.parent
        return list(reversed(path))


class TaskPlacement(models.Model):
    """Размещение задачи в структуре (связь многие-ко-многим)"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='placements')
    structure_node = models.ForeignKey(ClassStructure, on_delete=models.CASCADE, related_name='task_placements')
    order = models.IntegerField('Порядок', default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'task_description_app_taskplacement'
        ordering = ['structure_node__level', 'order']
        indexes = [
            models.Index(fields=['structure_node']),
            models.Index(fields=['task']),
        ]
        unique_together = ['task', 'structure_node']  # задача может быть размещена в узле только один раз

    def __str__(self):
        return f"{self.task} -> {self.structure_node}"
