import json

from django.db import models
from django.contrib.auth.models import AbstractUser, Group as AuthGroup
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator


# Кастомная модель пользователя
class User(AbstractUser):
    USER_TYPES = (
        ('teacher', 'Учитель'),
        ('student', 'Ученик'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    middle_name = models.CharField('Отчество', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()


# Класс (например, 10А, 9Б)
class SchoolClass(models.Model):
    number = models.IntegerField('Номер класса', validators=[MinValueValidator(1), MaxValueValidator(11)])
    letter = models.CharField('Буква класса', max_length=2)  # А, Б, В и т.д.

    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        unique_together = ['number', 'letter']

    def __str__(self):
        return f"{self.number}{self.letter}"




# Группа внутри класса (1 или 2)
class Group(models.Model):
    GROUP_NUMBERS = (
        (1, 'Группа 1'),
        (2, 'Группа 2'),
    )

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='groups')
    number = models.IntegerField('Номер группы', choices=GROUP_NUMBERS)
    teacher = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_groups',
        limit_choices_to={'user_type': 'teacher'}
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        unique_together = ['school_class', 'number']

    def __str__(self):
        return f"{self.school_class} - Группа {self.number}"


# Профиль ученика (расширение User)
class StudentProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='student_profile')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, related_name='students')

    # Дополнительные поля ученика
    solved_tasks = models.IntegerField('Решено задач', default=0)

    # ПОЛЕ СО СПИСКОМ ID ЗАДАЧ (реальных ID задач из UploadedProgram.task_id)
    solved_tasks_list = models.TextField(
        'Список решенных задач',
        default='[]',
        blank=True,
        help_text='JSON-список ID решенных задач (из UploadedProgram.task_id)'
    )

    class Meta:
        verbose_name = 'Профиль ученика'
        verbose_name_plural = 'Профили учеников'

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} - {self.group}"

    # МЕТОДЫ ДЛЯ РАБОТЫ СО СПИСКОМ РЕШЕННЫХ ЗАДАЧ

    def _get_tasks_list(self):
        """Внутренний метод: преобразует JSON строку в список"""
        try:
            return json.loads(self.solved_tasks_list)
        except (json.JSONDecodeError, TypeError):
            return []

    def _set_tasks_list(self, tasks):
        """Внутренний метод: преобразует список в JSON строку"""
        self.solved_tasks_list = json.dumps(tasks)

    def add_solved_task(self, real_task_id):
        """
        Добавляет реальный ID задачи в список решенных
        real_task_id - это значение из UploadedProgram.task_id (например, "34")
        """
        tasks = self._get_tasks_list()

        # Преобразуем в строку для единообразия
        task_id_str = str(real_task_id)

        if task_id_str not in tasks:
            tasks.append(task_id_str)
            self._set_tasks_list(tasks)
            self.solved_tasks = len(tasks)
            self.save()
            return True
        return False

    def remove_solved_task(self, real_task_id):
        """Удаляет ID задачи из списка решенных"""
        tasks = self._get_tasks_list()
        task_id_str = str(real_task_id)

        if task_id_str in tasks:
            tasks.remove(task_id_str)
            self._set_tasks_list(tasks)
            self.solved_tasks = len(tasks)
            self.save()
            return True
        return False

    def is_task_solved(self, real_task_id):
        """Проверяет, решена ли задача по её реальному ID"""
        tasks = self._get_tasks_list()
        return str(real_task_id) in tasks

    def get_solved_tasks(self):
        """Возвращает список ID решенных задач"""
        return self._get_tasks_list()

    def get_solved_tasks_count(self):
        """Возвращает количество решенных задач"""
        return len(self._get_tasks_list())

    def clear_solved_tasks(self):
        """Очищает список решенных задач"""
        self._set_tasks_list([])
        self.solved_tasks = 0
        self.save()

    def get_solved_tasks_display(self):
        """Возвращает строку для отображения в админке"""
        tasks = self._get_tasks_list()
        if tasks:
            if len(tasks) > 5:
                return f"{len(tasks)} задач: {', '.join(tasks[:5])}..."
            return f"{len(tasks)} задач: {', '.join(tasks)}"
        return "Нет решенных задач"

# Профиль учителя (расширение User)
class TeacherProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='teacher_profile')
    # Дополнительные поля учителя
    phone = models.CharField('Телефон', max_length=20, blank=True)
    subjects = models.CharField('Предметы', max_length=200, blank=True, help_text="Через запятую")

    class Meta:
        verbose_name = 'Профиль учителя'
        verbose_name_plural = 'Профили учителей'

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}"

    def get_groups(self):
        """Возвращает все группы учителя"""
        return Group.objects.filter(teacher=self.user)

    def get_students(self):
        """Возвращает всех учеников учителя"""
        return User.objects.filter(
            user_type='student',
            student_profile__group__teacher=self.user
        ).distinct()
