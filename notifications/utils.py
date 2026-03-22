from .models import Notification
from django.contrib.auth import get_user_model
from django.utils import timezone


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

        # print(f"✅ Уведомление создано для учителя {teacher.username}")
        return notification

    except Exception as e:
        print(f"❌ Ошибка создания уведомления: {e}")
        return None


def notify_student_about_assignment(student, collection):
    """
    Отправляет уведомление ученику о новой выданной контрольной работе
    """
    try:
        # Проверяем, есть ли уже такое уведомление
        existing = Notification.objects.filter(
            recipient=student,
            notification_type='collection_assigned',
            task_id=str(collection.id)
        ).exists()

        if existing:
            return None

        # Формируем сообщение
        title = f"📚 Новая контрольная работа: {collection.title}"
        message = (
            f"Вам выдана контрольная работа: {collection.title}\n\n"
            f"📝 Задач: {collection.collection_items.count()}\n"
            f"⭐ Максимальный балл: {collection.get_total_score()}\n"
        )

        if collection.time_limit:
            message += f"⏱️ Время выполнения: {collection.time_limit} минут\n"

        if collection.due_date:
            message += f"📅 Срок выполнения: {collection.due_date.strftime('%d.%m.%Y %H:%M')}\n"

        message += f"\nПерейдите в раздел 'Мои задания' для выполнения."

        # Создаем уведомление
        notification = Notification.objects.create(
            recipient=student,
            notification_type='collection_assigned',
            title=title,
            message=message,
            task_id=str(collection.id)
        )

        return notification

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка создания уведомления о назначении КР: {e}")
        return None


def notify_teacher_about_completed_assignment(teacher, student, collection, attempt):
    """
    Уведомляет учителя о том, что ученик выполнил контрольную работу
    """
    try:
        title = f"✅ Выполнена контрольная работа: {collection.title}"
        message = (
            f"Ученик {student.last_name} {student.first_name} "
            f"выполнил контрольную работу '{collection.title}'.\n\n"
            f"Результат: {attempt.score}/{attempt.max_score} баллов "
            f"({attempt.get_progress_percent()}%)\n"
        )

        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='collection_completed',
            title=title,
            message=message,
            task_id=str(collection.id)
        )

        return notification

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка создания уведомления о выполнении КР: {e}")
        return None