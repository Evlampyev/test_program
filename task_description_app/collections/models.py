# collections_app/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from task_description_app.tasks.models import Task


# Контрольная работа или свой урок
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
        db_table = 'task_description_app_collection'
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
        db_table = 'task_description_app_collectionitem'
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
        db_table = 'task_description_app_collectionattempt'
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
        db_table = 'task_description_app_collectionassignment'
        ordering = ['-assigned_at']
        unique_together = ['collection', 'student']

    def __str__(self):
        return f"{self.collection.title} -> {self.student.username}"

    def is_overdue(self):
        """Проверяет, просрочено ли задание"""
        if self.due_date and self.status != 'completed' and timezone.now() > self.due_date:
            return True
        return False
