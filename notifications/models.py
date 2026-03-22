from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import pytz

User = get_user_model()


class Notification(models.Model):
    """Модель уведомлений"""
    NOTIFICATION_TYPES = (
        ('task_solved', '✅ Задача решена'),
        ('task_attempt', '📝 Попытка решения'),
        ('student_registered', '👤 Новый ученик'),
        ('collection_assigned', '📚 Выдана контрольная работа'),
        ('collection_completed', '🎉 Контрольная выполнена'),
        ('system', '🔔 Системное'),
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель',
        limit_choices_to={'user_type': 'teacher'}
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        verbose_name='Ученик',
        limit_choices_to={'user_type': 'student'}
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='task_solved',
        verbose_name='Тип'
    )
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')

    # Данные задачи
    task_id = models.CharField(max_length=50, verbose_name='ID задачи')
    task_level = models.CharField(max_length=50, blank=True, null=True, verbose_name='Уровень')

    # Статус
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Создано')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    # def __str__(self):
    #     return f"{self.title} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def get_local_time(self):
        """Вспомогательный метод для получения локального времени"""
        return timezone.localtime(self.created_at)

    def get_formatted_time(self, format='%d.%m.%Y %H:%M'):
        """Форматированное локальное время"""
        return self.get_local_time().strftime(format)
