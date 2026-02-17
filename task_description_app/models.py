# models.py (или в соответствующем приложении)
import os

from django.db import models
from django.conf import settings


class Task(models.Model):
    """Модель задачи"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    md_file = models.FileField(upload_to='tasks/md/', help_text='Markdown файл с описанием задачи')
    test_file = models.FileField(upload_to='tasks/tests/', help_text='Python файл с тестами')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def md_path(self):
        """Полный путь к MD файлу"""
        if self.md_file:
            return os.path.join(settings.MEDIA_ROOT, self.md_file.name)
        return None

    @property
    def test_path(self):
        """Полный путь к файлу тестов"""
        if self.test_file:
            return os.path.join(settings.MEDIA_ROOT, self.test_file.name)
        return None


class UploadedProgram(models.Model):
    """Модель загруженной программы ученика"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='solutions')
    program_file = models.FileField(upload_to='student_programs/%Y/%m/%d/')
    program_path = models.CharField(max_length=500, blank=True)  # Абсолютный путь
    upload_time = models.DateTimeField(auto_now_add=True)
    test_results = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('uploaded', 'Загружено'),
            ('testing', 'Тестируется'),
            ('passed', 'Пройдено'),
            ('failed', 'Не пройдено'),
        ],
        default='uploaded'
    )

    def save(self, *args, **kwargs):
        # Сохраняем абсолютный путь при сохранении
        if self.program_file and not self.program_path:
            self.program_path = os.path.join(settings.MEDIA_ROOT, self.program_file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.task.title} - {self.upload_time}"