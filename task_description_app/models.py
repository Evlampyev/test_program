# models.py (или в соответствующем приложении)
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
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
        ('very_hard', 'Очень сложный'),
        ('expert', 'Эксперт'),
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


class ClassStructure(models.Model):
    """Структура классов/тем/уроков (только для навигации)"""
    name = models.CharField('Название', max_length=200)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.IntegerField('Уровень вложенности', default=0)  # 0-класс, 1-тема, 2-урок, 3-уровень
    order = models.IntegerField('Порядок', default=0)

    class Meta:
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
        ordering = ['structure_node__level', 'order']
        indexes = [
            models.Index(fields=['structure_node']),
            models.Index(fields=['task']),
        ]
        unique_together = ['task', 'structure_node']  # задача может быть размещена в узле только один раз

    def __str__(self):
        return f"{self.task} -> {self.structure_node}"


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

    def save(self, *args, **kwargs):
        # Сохраняем абсолютный путь при сохранении
        if self.program_file and not self.program_path:
            self.program_path = os.path.join(settings.MEDIA_ROOT, self.program_file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.task.title} - {self.upload_time}"


# Конртрольная работа или свой урок
class Collection(models.Model):
    """Подборка задач (контрольная работа, урок)"""
    COLLECTION_TYPES = (
        ('lesson', 'Урок'),
        ('test', 'Контрольная работа'),
        ('exam', 'Экзамен'),
        ('homework', 'Домашнее задание'),
    )

    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    collection_type = models.CharField('Тип', max_length=20, choices=COLLECTION_TYPES, default='lesson')

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_collections'
    )

    # Для кого предназначена подборка
    target_class = models.CharField('Класс', max_length=50, blank=True)
    target_group = models.IntegerField('Группа', null=True, blank=True)

    # Настройки
    is_public = models.BooleanField('Публичная', default=True)
    show_results = models.BooleanField('Показывать результаты', default=True)
    time_limit = models.IntegerField('Ограничение времени (мин)', null=True, blank=True)

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Задачи (ManyToMany через промежуточную модель)
    tasks = models.ManyToManyField(Task, through='CollectionItem', related_name='collections')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Подборка задач'
        verbose_name_plural = 'Подборки задач'

    def __str__(self):
        return f"{self.get_collection_type_display()}: {self.title}"

    def get_total_score(self):
        """Общая сумма баллов"""
        return sum(item.max_score for item in self.collection_items.all())

    def get_task_count(self):
        """Количество задач"""
        return self.collection_items.count()

    def is_available_for_student(self, student):
        """Проверяет, доступна ли подборка для ученика"""
        if not self.is_public and self.author != student:
            return False

        # Проверка по классу и группе
        if self.target_class and hasattr(student, 'student_profile'):
            student_group = student.student_profile.group
            if student_group and student_group.school_class:
                # Сравниваем класс (например, "10 класс" с "10")
                class_num = ''.join(filter(str.isdigit, self.target_class))
                if class_num and str(student_group.school_class.number) != class_num:
                    return False

            # Проверка группы
            if self.target_group and student_group and student_group.number != self.target_group:
                return False

        return True

    def get_available_students(self):
        """Возвращает список учеников, которым доступна подборка"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        students = User.objects.filter(user_type='student')

        if self.target_class:
            class_num = ''.join(filter(str.isdigit, self.target_class))
            students = students.filter(
                student_profile__group__school_class__number=class_num
            )

        if self.target_group:
            students = students.filter(student_profile__group__number=self.target_group)

        return students


class CollectionItem(models.Model):
    """Задача в подборке"""
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='collection_items'
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    order = models.IntegerField('Порядок', default=0)
    max_score = models.IntegerField('Максимальный балл', default=10)
    required = models.BooleanField('Обязательная', default=True)

    class Meta:
        ordering = ['order']
        unique_together = ['collection', 'task']

    def __str__(self):
        return f"{self.order}. {self.task.title} ({self.max_score} баллов)"


class CollectionAttempt(models.Model):
    """Попытка выполнения подборки учеником"""
    STATUS_CHOICES = (
        ('in_progress', 'В процессе'),
        ('completed', 'Завершена'),
        ('graded', 'Проверена'),
    )

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collection_attempts')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='in_progress')

    score = models.IntegerField('Баллы', default=0)
    max_score = models.IntegerField('Максимум', default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Попытка выполнения'
        verbose_name_plural = 'Попытки выполнения'

    def __str__(self):
        return f"{self.student} - {self.collection.title} ({self.score}/{self.max_score})"

    def get_progress_percent(self):
        """Процент выполнения"""
        if self.max_score > 0:
            return round((self.score / self.max_score) * 100)
        return 0


class CollectionAssignment(models.Model):
    """Назначение контрольной работы ученику"""
    STATUS_CHOICES = (
        ('pending', 'Ожидает выполнения'),
        ('in_progress', 'Выполняется'),
        ('completed', 'Выполнено'),
        ('expired', 'Просрочено'),
    )

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='collection_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField('Срок выполнения', null=True, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-assigned_at']
        unique_together = ['collection', 'student']

    def __str__(self):
        return f"{self.collection.title} -> {self.student.username}"

    def is_overdue(self):
        """Проверяет, просрочено ли задание"""
        if self.due_date and timezone.now() > self.due_date:
            return True
        return False