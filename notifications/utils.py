from .models import Notification
from django.contrib.auth import get_user_model


User = get_user_model()


def create_task_solved_notification(task_attempt):
    """
    Создает уведомление для учителя о решенной задаче
    """
    try:
        student = task_attempt.user

        # Проверяем, что у ученика есть профиль и группа
        if not hasattr(student, 'student_profile'):
            print("❌ У ученика нет профиля")
            return None

        student_group = student.student_profile.group
        if not student_group:
            print("❌ У ученика нет группы")
            return None

        teacher = student_group.teacher
        if not teacher:
            print("❌ У группы нет учителя")
            return None

        # Проверяем, нет ли уже такого уведомления (чтобы не дублировать)
        existing = Notification.objects.filter(
            recipient=teacher,
            sender=student,
            task_id=str(task_attempt.real_task_id),
            notification_type='task_solved'
        ).exists()

        if existing:
            print("⏭️ Уведомление уже существует")
            return None
        from users_app.views import get_task_level, get_task_title

        # Формируем сообщение
        class_info = f"{student_group.school_class}" if student_group.school_class else "Класс не указан"

        title = f"✅ Задача решена: {student.last_name} {student.first_name}"
        message = (
            # f"Ученик {student.last_name} {student.first_name} "
            f"Класс {class_info}, группа {student_group.number}. "
            f"Задача #{task_attempt.real_task_id} '{get_task_title(task_attempt.real_task_id)}'"
        )

        # Создаем уведомление
        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='task_solved',
            title=title,
            message=message,
            task_id=str(task_attempt.real_task_id),
            task_level=get_task_level(task_attempt.real_task_id)
        )

        print(f"✅ Уведомление создано для учителя {teacher.username}")
        return notification

    except Exception as e:
        print(f"❌ Ошибка создания уведомления: {e}")
        return None
