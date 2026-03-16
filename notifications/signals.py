from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from django.utils import timezone

User = get_user_model()


@receiver(post_save)
def notify_on_task_solved(sender, **kwargs):
    """Уведомление только от TaskAttempt"""

    # Проверяем, что это модель TaskAttempt
    if sender.__name__ != 'TaskAttempt':
        return

    instance = kwargs.get('instance')

    # Проверяем, что задача решена
    if not instance.is_solved:
        return

    # print(f"📨 Задача решена! Ученик: {instance.user.username}, задача: {instance.real_task_id}")

    try:
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from .utils import create_task_solved_notification

        # Создаем уведомление
        notification = create_task_solved_notification(instance)

        # if notification:
        #     print(f"✅ Уведомление создано: ID {notification.id}")
        # else:
        #     print("❌ Уведомление не создано")

    except Exception as e:
        print(f"❌ Ошибка в сигнале: {e}")
        import traceback
        traceback.print_exc()
