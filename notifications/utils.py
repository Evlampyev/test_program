import pytz
from django.conf import settings

from task_description_app.collections import Collection, CollectionAttempt
from task_description_app.models import Task
from users_app.models import TeacherProfile, StudentProfile
from .models import Notification
from django.contrib.auth import get_user_model
from django.utils import timezone

from manage import logger

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
            f"{class_info} (группа {student_group.number}). "
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


def notify_teacher_about_task_solved(student, task_id, task_level=None, task_title=None):
    """
    Отправляет уведомление учителю о решенной задаче

    Args:
        student: Объект User ученика
        task_id: ID задачи (строка или число)
        task_level: Уровень сложности задачи (опционально)
        task_title: Название задачи (опционально)

    Returns:
        Notification: Созданное уведомление или None
    """
    try:
        # Проверяем, есть ли у ученика группа и учитель
        if not hasattr(student, 'student_profile'):
            logger.warning(f"У ученика {student.username} нет профиля")
            return None

        student_group = student.student_profile.group
        if not student_group:
            logger.warning(f"У ученика {student.username} нет группы")
            return None

        teacher = student_group.teacher
        if not teacher:
            logger.warning(f"У группы {student_group} нет учителя")
            return None

        # Проверяем, не было ли уже уведомления для этой задачи (чтобы не дублировать)
        existing = Notification.objects.filter(
            recipient=teacher,
            sender=student,
            task_id=str(task_id),
            notification_type='task_solved'
        ).exists()

        if existing:
            logger.info(f"Уведомление для задачи {task_id} уже существует, пропускаем")
            return None

        # Формируем информацию о классе
        class_info = f"{student_group.school_class}" if student_group.school_class else "Класс не указан"

        # Формируем заголовок и сообщение
        title = f"✅ Задача решена: {student.last_name} {student.first_name}"

        task = Task.objects.filter(task_id=str(task_id)).first()

        message = (
            f"Ученик {student.last_name} {student.first_name} "
            f"{class_info} ({student_group.number}) "
            f"успешно решил задачу #{task_id}"
        )

        if task_level:
            message += f" (уровень {task_level})"

        if task.title:
            message += f"\n\n📌 Задача: {task.title}"

        # print(f"!!!!!!! from notifications {student=}, and {student.id =} !!!!!!!!!!!")
        # Создаем уведомление
        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='task_solved',
            title=title,
            message=message,
            task_id=str(task_id),
            task_level=task_level,
            # student_id=student.id
        )

        logger.info(f"Уведомление создано для учителя {teacher.username} о задаче #{task_id}")
        return notification

    except Exception as e:
        logger.error(f"Ошибка при создании уведомления о решенной задаче: {e}")
        import traceback
        traceback.print_exc()
        return None


def notify_teacher_about_task_attempt(student, task_id, attempt_count, task_level=None):
    """
    Отправляет уведомление учителю о попытке решения задачи

    Args:
        student: Объект User ученика
        task_id: ID задачи
        attempt_count: Номер попытки
        task_level: Уровень сложности
    """
    try:
        if not hasattr(student, 'student_profile'):
            return None

        student_group = student.student_profile.group
        if not student_group or not student_group.teacher:
            return None

        teacher = student_group.teacher
        from users_app.views import get_task_title
        message = (
            f"{student_group.school_class} (группа {student_group.number}). "

            f"Задача #{task_id} '{get_task_title(task_id)}'"
            f" Попытка {attempt_count}-я."
        )

        status = "📝 попытка решения"
        title = f"{status} задачи: {student.last_name} {student.first_name}"

        if not task_level:
            from users_app.views import get_task_level
            task_level = get_task_level(task_id)

        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='task_attempt',
            title=title,
            message=message,
            task_level=task_level,
            task_id=str(task_id),
        )

        return notification

    except Exception as e:
        logger.error(f"Ошибка при создании уведомления о попытке: {e}")
        return None


def notify_teacher_about_completed_assignment(teacher, student, collection: Collection,
                                              attempt: CollectionAttempt):
    """
    Уведомляет учителя о том, что ученик выполнил контрольную работу

    Args:
        teacher: Объект User учителя
        student: Объект User ученика
        collection: Объект Collection
        attempt: Объект CollectionAttempt
    """
    # print("notify_teacher_about_completed_assignment", student)
    try:
        # Проверяем, что учитель существует
        if not teacher:
            # print("Учитель не найден")
            return None

        title = f"🚩 Выполнена КР: {collection.title}"
        # Получаем человеко-читаемое название типа
        collection_type_display = collection.get_collection_type_display()

        message = (
            f" {student.last_name} {student.first_name} "
            # f"выполнил КР '{collection.title}'.\n\n"
            f"Результат: {attempt.score}/{attempt.max_score} баллов "
            f"({attempt.get_progress_percent()}%)\n"
        )

        # if attempt.completed_at:
        #     message += f"📅 {timezone.localtime(attempt.completed_at).strftime('%d.%m.%Y %H:%M')}\n"

        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='collection_completed',
            title=title,
            message=message,
            task_id=str(collection.id),
            task_level=collection_type_display
        )

        return notification

    except Exception as e:
        logger.error(f"Ошибка создания уведомления о выполнении КР: {e}")
        print(f"Ошибка создания уведомления о выполнении КР: {e}")
        import traceback
        traceback.print_exc()
        return None


def notify_student_about_result(student, task_id, result):
    """
    Отправляет уведомление ученику о результате проверки задачи

    Args:
        student: Объект User ученика
        task_id: ID задачи
        result: Результат проверки ('correct' или 'incorrect')
    """
    try:
        if not hasattr(student, 'student_profile'):
            return None

        is_correct = (result == 'correct')

        title = "✅ Задача решена верно!" if is_correct else "❌ Задача решена неверно"

        message = (
            f"Ваше решение задачи #{task_id} "
            f"{'принято' if is_correct else 'не принято'}. "
            f"{'Поздравляем!' if is_correct else 'Попробуйте еще раз.'}"
        )

        notification = Notification.objects.create(
            recipient=student,
            notification_type='task_attempt',
            title=title,
            message=message,
            task_id=str(task_id)
        )

        return notification

    except Exception as e:
        logger.error(f"Ошибка при создании уведомления ученику: {e}")
        return None


def notify_student_about_assignment(student, collection):
    """
    Отправляет уведомление ученику о новой выданной контрольной работе

    Args:
        student: Объект User ученика
        collection: Объект Collection (подборка задач)
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
        logger.error(f"Ошибка создания уведомления о назначении КР: {e}")
        return None


def notify_new_student_registration(teacher, student):
    """
    Уведомляет учителя о новом ученике в его группе

    Args:
        teacher: Объект User учителя
        student: Объект User нового ученика
    """
    try:
        title = f"👤 Новый ученик в группе"
        message = (
            f"В вашу группу добавился новый ученик:\n"
            f"{student.last_name} {student.first_name} {student.middle_name}\n"
            f"Логин: {student.username}"
        )

        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='student_registered',
            title=title,
            message=message,
            # student_id=student.id
        )

        return notification

    except Exception as e:
        logger.error(f"Ошибка создания уведомления о новом ученике: {e}")
        return None


def notify_teacher_about_time_request(teacher, student, collection, assignment, message=''):
    """
    Уведомляет учителя о запросе ученика на продление времени

    Args:
        teacher: Объект User учителя
        student: Объект User ученика
        collection: Объект Collection (подборка задач)
        assignment: Объект CollectionAssignment (назначение)
        message: Текст сообщения от ученика

    Returns:
        Notification: Созданное уведомление или None
    """
    try:
        from .models import Notification
        from django.utils import timezone
        import pytz

        # Активируем часовой пояс
        if hasattr(teacher, 'timezone') and teacher.timezone:
            user_timezone = pytz.timezone(teacher.timezone)
            timezone.activate(user_timezone)
        else:
            timezone.activate(pytz.timezone(settings.TIME_ZONE))

        title = f"⏰ Запрос на продление времени: {student.last_name} {student.first_name}"

        message_text = (
            # f"Ученик {student.last_name} {student.first_name} "
            # f"просит продлить время на выполнение задания:\n\n"
            f"📚 {collection.title}<br>"
        )

        if assignment.due_date:
            message_text += f"📅 Текущий срок: {timezone.localtime(assignment.due_date).strftime('%d.%m.%Y %H:%M')}<br>"

        if message:
            message_text += f"💬 Сообщение от ученика:\n{message}"

        # message_text += f"\n🔗 Для продления срока перейдите в настройки задания."

        # Проверяем, нет ли уже непрочитанного запроса по этому заданию
        existing = Notification.objects.filter(
            recipient=teacher,
            sender=student,
            notification_type='time_request',
            task_id=str(collection.id),
            is_read=False
        ).first()

        if existing:
            # Обновляем существующее уведомление
            existing.message = message_text
            existing.created_at = timezone.now()
            existing.save()
            return existing

        # Получаем человеко-читаемое название типа
        collection_type_display = collection.get_collection_type_display()

        # Создаем новое уведомление
        notification = Notification.objects.create(
            recipient=teacher,
            sender=student,
            notification_type='time_request',
            title=title,
            message=message_text,
            task_id=str(collection.id),
            task_level=collection_type_display,
        )

        timezone.deactivate()
        return notification

    except Exception as e:
        print(f"Ошибка создания уведомления о запросе времени: {e}")
        return None
