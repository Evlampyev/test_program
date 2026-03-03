from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TaskAttempt, UploadedProgram, StudentProfile

# не нужен, без него реализовал


@receiver(post_save, sender=TaskAttempt)
def update_solved_tasks(sender, instance, created, **kwargs):
    """
    При создании новой попытки с is_solved=True:
    1. Находим соответствующую программу (UploadedProgram)
    2. Берем оттуда реальный ID задачи
    3. Добавляем его в список решенных задач ученика
    """
    print(f"Сигнал сработал! created={created}, is_solved={instance.is_solved}")
    if created and instance.is_solved:
        try:
            profile = instance.user.student_profile

            # Получаем реальный ID задачи
            # Вариант 1: если в TaskAttempt есть поле program
            if hasattr(instance, 'program') and instance.program:
                real_task_id = instance.program.task_id
            else:
                # Вариант 2: если есть поле real_task_id
                real_task_id = getattr(instance, 'real_task_id', instance.task_id)

            # Добавляем задачу в список решенных
            profile.add_solved_task(real_task_id)

            # Можно добавить логирование
            print(f"Задача {real_task_id} добавлена в список решенных ученика {profile.user.username}")

        except StudentProfile.DoesNotExist:
            # У пользователя нет профиля ученика (возможно это учитель)
            pass
        except Exception as e:
            # Логируем другие ошибки
            print(f"Ошибка в сигнале update_solved_tasks: {e}")
