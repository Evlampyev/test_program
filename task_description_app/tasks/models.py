import os

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
import pytz

User = get_user_model()


class DifficultyLevel(models.Model):
    """
    Модель уровней сложности задач
    """
    DIFFICULTY_CHOICES = [
        ('A', 'Легкий'),
        ('B', 'Средний'),
        ('C', 'Сложный'),
        ('D', 'Очень сложный'),
        ('E', 'Эксперт'),
    ]

    COLOR_CHOICES = [
        ('success', 'Зеленый (Easy)'),
        ('warning', 'Желтый (Medium)'),
        ('danger', 'Красный (Hard)'),
        ('brown', 'Коричневый (Very_Hard)'),
        ('dark', 'Черный (Expert)'),
    ]

    level_name = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        unique=True,
        verbose_name='Уровень сложности'
    )
    display_name = models.CharField(
        max_length=50,
        verbose_name='Отображаемое название'
    )
    level_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )
    color_code = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default='secondary',
        verbose_name='Цвет для отображения'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание уровня'
    )

    class Meta:
        db_table = 'task_description_app_difficultylevel'
        verbose_name = 'Уровень сложности'
        verbose_name_plural = 'Уровни сложности'
        ordering = ['level_order', 'id']

    def __str__(self):
        return self.display_name or self.get_level_name_display()

    @property
    def task_count(self):
        """Количество задач этого уровня"""
        return self.tasks.count()

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.get_level_name_display()
        super().save(*args, **kwargs)


class Task(models.Model):
    """Модель задачи"""
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Название задачи'
    )
    description = models.TextField(
        verbose_name="Описание",
        blank=True
    )
    difficulty = models.ForeignKey(
        DifficultyLevel,
        on_delete=models.PROTECT,
        related_name='tasks',
        verbose_name='Уровень сложности'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(
        verbose_name='Публичная',
        default=True
    )

    # Файлы задачи
    test_files = models.JSONField(
        verbose_name='Файлы тестов',
        default=list
    )  # список файлов

    # Статистика выполнения
    total_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='Всего попыток'
    )
    perfect_solutions = models.PositiveIntegerField(
        default=0,
        verbose_name='Успешных на 100% попыток'
    )

    # Временные метки
    last_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        auto_now_add=True,
        verbose_name='Последняя попытка'
    )

    class Meta:
        db_table = 'task_description_app_task'

    def __str__(self):
        return f"#{self.id}: {self.title}"

    def get_files_path(self):
        """Возвращает путь к папке с файлами задачи"""
        return os.path.join('tasks', str(self.id))

    def increment_usage(self):
        """Увеличить счетчик использования"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    @property
    def perfect_rate(self):
        """Процент 100% успешных решений"""
        if self.total_attempts > 0:
            return round((self.perfect_solutions / self.total_attempts) * 100, 1)
        return 0.0

    def update_statistics(self, task_result):
        """
        Обновление статистики после новой попытки
        """
        # Активируем нужный часовой пояс для текущего потока
        timezone.activate(pytz.timezone(settings.TIME_ZONE))

        # Обновляем счетчики
        self.total_attempts += 1
        self.last_attempt_at = timezone.now()
        if task_result == 'passed':
            self.perfect_solutions += 1

        self.save()

        # Деактивируем (опционально)
        timezone.deactivate()


# Модель для отслеживания попыток решения
class TaskAttempt(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает проверки'),
        ('correct', 'Верно'),
        ('incorrect', 'Неверно'),
        ('error', 'Ошибка'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_attempts')
    task_path = models.CharField('Путь к задаче', max_length=500)  # путь к папке задачи
    task_id = models.CharField('ID задания', max_length=50)  # Непонятное число , нужно удалить
    attempt_time = models.DateTimeField('Время попытки', default=timezone.now)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    code = models.TextField('Код решения', blank=True)
    result = models.TextField('Результат', blank=True)
    is_solved = models.BooleanField('Решено', default=False)  # флаг, что задача решена (для статистики)
    real_task_id = models.CharField('ID задачи', max_length=50, blank=True)

    class Meta:
        db_table = 'task_description_app_taskattempt'
        ordering = ['-attempt_time']
        verbose_name = 'Попытка решения'
        verbose_name_plural = 'Попытки решения'

    def __str__(self):
        return f"{self.user.username} - {self.real_task_id} - {self.get_local_time()}"

    def get_local_time(self):
        """Вспомогательный метод для получения локального времени"""
        return timezone.localtime(self.attempt_time)


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

    class Meta:
        db_table = 'task_description_app_uploadedprogram'

    def __str__(self):
        return f"{self.user} - {self.task.title} - {self.upload_time}"

    def save(self, *args, **kwargs):
        # Сохраняем абсолютный путь при сохранении
        if self.program_file and not self.program_path:
            self.program_path = os.path.join(settings.MEDIA_ROOT, self.program_file.name)
        super().save(*args, **kwargs)
