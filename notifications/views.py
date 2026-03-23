from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.csrf import csrf_protect
import pytz

from .models import Notification
from django.utils import timezone


@login_required
@ensure_csrf_cookie
def get_notifications(request):
    """API для получения уведомлений"""

    # Активируем часовой пояс пользователя
    timezone.activate(pytz.timezone(settings.TIME_ZONE))

    if request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    try:
        # Получаем последние 50 уведомлений
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related('sender')[:50]

        # Считаем непрочитанные
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        data = {
            'unread_count': unread_count,
            'notifications': [
                {
                    'id': n.id,
                    'title': n.title,
                    'message': n.message,
                    'task_id': n.task_id,
                    'task_level': n.task_level,
                    'is_read': n.is_read,
                    'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
                }
                for n in notifications
            ]
        }
        timezone.deactivate()
        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def mark_as_read(request, notification_id):
    """Отметить одно уведомление как прочитанное"""
    if request.user.user_type != 'teacher':
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.mark_as_read()
        return JsonResponse({'success': True})

    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Уведомление не найдено'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
@csrf_protect
def mark_all_as_read(request):
    """Отметить все уведомления как прочитанные"""
    try:
        # Проверяем, что пользователь - учитель
        if request.user.user_type != 'teacher':
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        # Отмечаем все непрочитанные уведомления
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        return JsonResponse({
            'success': True,
            'marked_count': count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


